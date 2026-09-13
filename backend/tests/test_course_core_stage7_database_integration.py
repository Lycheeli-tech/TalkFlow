import os
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.ai.fakes import FakeSpeechToTextService, FakeTextToSpeechService
from app.core.config import get_settings
from app.course.answer_service import CourseAnswerService
from app.course.catalog_v1 import COURSE_CATALOG_V1
from app.course.chinese_organizer import FakeChineseAnswerOrganizer
from app.course.repository import SQLCourseAnswerRepository
from app.course.storage import FakeCourseAudioStorage


async def legacy_snapshot(session):
    progress = (
        await session.execute(
            text(
                "select id,current_day,current_phase,xp,current_streak "
                "from public.users order by id"
            )
        )
    ).all()
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
    return progress, counts


@pytest.mark.skipif(
    os.getenv("RUN_COURSE_CORE_DB_INTEGRATION") != "1", reason="opt-in real PostgreSQL"
)
@pytest.mark.asyncio
async def test_all_questions_persist_and_new_courses_confirm_without_legacy_writes_rollback():
    engine = create_async_engine(get_settings().database_url)
    try:
        async with engine.connect() as connection:
            transaction = await connection.begin()
            try:
                async with AsyncSession(
                    bind=connection,
                    expire_on_commit=False,
                    join_transaction_mode="create_savepoint",
                ) as session:
                    owners = (
                        await session.scalars(
                            text("select id from public.users order by id limit 2")
                        )
                    ).all()
                    if len(owners) < 2:
                        pytest.skip("requires two existing test users")
                    owner, other = owners
                    before = await legacy_snapshot(session)
                    repo = SQLCourseAnswerRepository(session)
                    service = CourseAnswerService(
                        repository=repo,
                        audio=FakeCourseAudioStorage(),
                        stt=FakeSpeechToTextService("This is a synthetic catalog contract test."),
                        chinese_stt=FakeSpeechToTextService("我负责测试。"),
                        tts=FakeTextToSpeechService(),
                        chinese_organizer=FakeChineseAnswerOrganizer(),
                    )
                    for course in COURSE_CATALOG_V1:
                        for question in course.questions:
                            saved = await service.submit_english(
                                user_id=owner,
                                course_id=course.id,
                                question_id=question.id,
                                idempotency_key=f"p7-db-{uuid4()}",
                                audio=b"synthetic-contract",
                                content_type="audio/webm",
                                duration_ms=1000,
                            )
                            assert saved.answer.status == "SAVED"
                            assert saved.answer.question_id == question.id
                            assert await repo.get(other, saved.answer.id) is None
                    for course_id, question_id in (
                        ("course-01", "course-01.follow-up"),
                        ("course-10", "course-10.core"),
                        ("course-29", "course-29.follow-up"),
                        ("course-30", "course-30.core"),
                    ):
                        draft = await service.submit_chinese(
                            user_id=owner,
                            course_id=course_id,
                            question_id=question_id,
                            idempotency_key=f"p7-chinese-db-{uuid4()}",
                            audio=b"synthetic-contract",
                            content_type="audio/webm",
                            duration_ms=1000,
                        )
                        assert draft.answer.status == "AWAITING_CONFIRMATION"
                        saved = await service.confirm(user_id=owner, answer_id=draft.answer.id)
                        assert saved.answer.status == "SAVED" and saved.answer.confirmed_at
                        assert (
                            saved.transcript.organized_english == "I was responsible for testing."
                        )
                    assert await legacy_snapshot(session) == before
                    # Same table policies protect Answers from every Course, including Course 30.
                    await session.execute(text("set local role authenticated"))
                    await session.execute(
                        text("select set_config('request.jwt.claim.sub',:owner,true)"),
                        {"owner": str(other)},
                    )
                    assert (
                        await session.scalar(
                            text("select count(*) from public.course_answers where user_id=:owner"),
                            {"owner": owner},
                        )
                        == 0
                    )
                    assert not await session.scalar(
                        text(
                            "select has_table_privilege("
                            "current_user,'public.course_answers','INSERT')"
                        )
                    )
                    await session.execute(text("reset role"))
            finally:
                await transaction.rollback()
    finally:
        await engine.dispose()
