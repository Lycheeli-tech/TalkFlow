import os
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.ai.fakes import FakeSpeechToTextService, FakeTextToSpeechService
from app.core.config import get_settings
from app.course.answer_service import CourseAnswerService
from app.course.chinese_organizer import FakeChineseAnswerOrganizer
from app.course.repository import SQLCourseAnswerRepository
from app.course.storage import FakeCourseAudioStorage

MIGRATION_SQL = (
    Path(__file__).resolve().parents[2]
    / "supabase/migrations/202609130020_chinese_answer_drafts.sql"
).read_text(encoding="utf-8")


async def snapshot(session, owner):
    progress = (
        await session.execute(
            text(
                "select current_day, current_phase, xp, current_streak "
                "from public.users where id=:id"
            ),
            {"id": owner},
        )
    ).one()
    counts = [
        await session.scalar(text(f"select count(*) from public.{table}"))
        for table in (
            "sessions",
            "attempts",
            "expressions",
            "expression_attempts",
            "retrieval_opportunities",
        )
    ]
    return tuple(progress), counts


@pytest.mark.skipif(
    os.getenv("RUN_COURSE_CORE_DB_INTEGRATION") != "1", reason="opt-in real PostgreSQL"
)
@pytest.mark.asyncio
async def test_chinese_draft_migration_confirmation_recovery_rls_and_legacy_snapshot_rollback():
    # All P6 DDL and synthetic rows roll back; never migrate production implicitly.
    engine = create_async_engine(get_settings().database_url)
    async with engine.connect() as connection:
        transaction = await connection.begin()
        try:
            column = await connection.scalar(
                text(
                    "select count(*) from information_schema.columns where table_schema='public' "
                    "and table_name='course_transcripts' and column_name='organizer_provider'"
                )
            )
            if not column:
                raw = await connection.get_raw_connection()
                await raw.driver_connection.execute(MIGRATION_SQL)
            session = AsyncSession(
                bind=connection, expire_on_commit=False, join_transaction_mode="create_savepoint"
            )
            async with session:
                owners = (
                    await session.scalars(text("select id from public.users order by id limit 2"))
                ).all()
                if len(owners) < 2:
                    pytest.skip("requires two existing test users")
                owner, other = owners
                before = await snapshot(session, owner)
                repo = SQLCourseAnswerRepository(session)
                prior_history = await repo.list_history(owner, "course-11.core")
                service = CourseAnswerService(
                    repository=repo,
                    stt=FakeSpeechToTextService("我负责测试。"),
                    tts=FakeTextToSpeechService(),
                    audio=FakeCourseAudioStorage(),
                    chinese_organizer=FakeChineseAnswerOrganizer(),
                )
                draft = await service.submit_chinese(
                    user_id=owner,
                    course_id="course-11",
                    question_id="course-11.core",
                    idempotency_key=f"p6-db-{uuid4()}",
                    audio=b"synthetic",
                    content_type="audio/webm",
                    duration_ms=1000,
                )
                assert draft.answer.status == "AWAITING_CONFIRMATION"
                assert await repo.list_history(owner, "course-11.core") == prior_history
                assert (await repo.list_drafts(owner, "course-11.core"))[
                    0
                ].answer.id == draft.answer.id
                assert await repo.get(other, draft.answer.id) is None
                await session.execute(text("set local role authenticated"))
                await session.execute(
                    text("select set_config('request.jwt.claim.sub', :id, true)"),
                    {"id": str(other)},
                )
                assert (
                    await session.scalar(
                        text("select count(*) from public.course_answers where id=:id"),
                        {"id": draft.answer.id},
                    )
                    == 0
                )
                await session.execute(
                    text("select set_config('request.jwt.claim.sub', :id, true)"),
                    {"id": str(owner)},
                )
                assert (
                    await session.scalar(
                        text("select count(*) from public.course_answers where id=:id"),
                        {"id": draft.answer.id},
                    )
                    == 1
                )
                await session.execute(text("reset role"))
                assert await snapshot(session, owner) == before
                saved = await service.confirm(user_id=owner, answer_id=draft.answer.id)
                assert saved.answer.status == "SAVED" and saved.answer.confirmed_at
                assert saved.transcript.organized_english == "I was responsible for testing."
                assert (
                    await service.confirm(user_id=owner, answer_id=draft.answer.id)
                ).answer.saved_sequence == saved.answer.saved_sequence
                assert await snapshot(session, owner) == before
                await service.delete(user_id=owner, answer_id=draft.answer.id)
                assert await snapshot(session, owner) == before
                # Owner-filtered authenticated reads and no direct product writes.
                await session.execute(text("set local role authenticated"))
                await session.execute(
                    text("select set_config('request.jwt.claim.sub', :id, true)"),
                    {"id": str(other)},
                )
                assert not await session.scalar(
                    text(
                        "select has_table_privilege("
                        "current_user, 'public.course_answers', 'UPDATE')"
                    )
                )
                assert (
                    await session.scalar(
                        text("select count(*) from public.course_answers where user_id=:id"),
                        {"id": owner},
                    )
                    == 0
                )
                await session.execute(text("reset role"))
        finally:
            await transaction.rollback()
    await engine.dispose()
