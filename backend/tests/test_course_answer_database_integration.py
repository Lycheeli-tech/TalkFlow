import os
from uuid import uuid4

import pytest
from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.ai.fakes import FakeSpeechToTextService, FakeTextToSpeechService
from app.core.config import get_settings
from app.course.answer_service import CourseAnswerService
from app.course.models import CourseAnswerRow
from app.course.repository import SQLCourseAnswerRepository
from app.course.storage import FakeCourseAudioStorage
from app.db.models import UserRow

LEGACY_TABLES = (
    "sessions",
    "attempts",
    "expressions",
    "expression_attempts",
    "retrieval_opportunities",
)


async def legacy_snapshot(connection, user_id):
    progress = await connection.fetchrow(
        """
        select current_day, current_phase, xp, current_streak
        from public.users where id = $1
        """,
        user_id,
    )
    counts = {
        table: await connection.fetchval(
            f"select count(*) from public.{table} where user_id = $1", user_id
        )
        for table in LEGACY_TABLES
    }
    return tuple(progress.values()), counts


async def sqlalchemy_legacy_snapshot(session, user_id):
    progress = (
        await session.execute(
            text(
                """
                select current_day, current_phase, xp, current_streak
                from public.users where id = :user_id
                """
            ),
            {"user_id": user_id},
        )
    ).one()
    counts = {}
    for table in LEGACY_TABLES:
        counts[table] = await session.scalar(
            text(f"select count(*) from public.{table} where user_id = :user_id"),
            {"user_id": user_id},
        )
    return tuple(progress), counts


@pytest.mark.skipif(
    os.getenv("RUN_COURSE_CORE_DB_INTEGRATION") != "1",
    reason="set RUN_COURSE_CORE_DB_INTEGRATION=1 to use the configured PostgreSQL test database",
)
@pytest.mark.asyncio
async def test_course_answer_rls_and_legacy_progress_isolation_in_rolled_back_database() -> None:
    engine = create_async_engine(get_settings().database_url)
    other_id, answer_id = uuid4(), uuid4()
    async with engine.connect() as sql_connection:
        raw_connection = await sql_connection.get_raw_connection()
        connection = raw_connection.driver_connection
        if await connection.fetchval("select to_regclass('public.course_answers')") is None:
            pytest.skip("apply the P3 Course Answer migration before running this integration test")
        transaction = connection.transaction()
        await transaction.start()
        try:
            owner_id = await connection.fetchval("select id from public.users order by id limit 1")
            if owner_id is None:
                pytest.skip("configured test database has no user fixture")
            before = await legacy_snapshot(connection, owner_id)

            await connection.execute(
                """
                insert into public.course_answers (
                  id, user_id, course_id, question_id, answer_language, status,
                  idempotency_key, saved_at, saved_sequence
                ) values (
                  $1, $2, 'course-11', 'course-11.core', 'ENGLISH', 'SAVED',
                  'database-isolation-check', now(),
                  nextval('public.course_answer_saved_sequence')
                )
                """,
                answer_id,
                owner_id,
            )
            await connection.execute(
                """
                insert into public.course_transcripts (
                  answer_id, user_id, source_language, transcript, stt_provider
                ) values ($1, $2, 'ENGLISH', 'Database isolation transcript.', 'test')
                """,
                answer_id,
                owner_id,
            )

            assert await legacy_snapshot(connection, owner_id) == before

            await connection.execute("set local role authenticated")
            await connection.execute(
                "select set_config('request.jwt.claim.sub', $1, true)", str(owner_id)
            )
            assert await connection.fetchval("select count(*) from public.course_answers") == 1
            assert await connection.fetchval("select count(*) from public.course_transcripts") == 1
            assert not await connection.fetchval(
                "select has_table_privilege(current_user, 'public.course_answers', 'INSERT')"
            )

            await connection.execute(
                "select set_config('request.jwt.claim.sub', $1, true)", str(other_id)
            )
            assert await connection.fetchval("select count(*) from public.course_answers") == 0
            assert await connection.fetchval("select count(*) from public.course_transcripts") == 0
        finally:
            await transaction.rollback()
    await engine.dispose()


@pytest.mark.skipif(
    os.getenv("RUN_COURSE_CORE_DB_INTEGRATION") != "1",
    reason="set RUN_COURSE_CORE_DB_INTEGRATION=1 to use the configured PostgreSQL test database",
)
@pytest.mark.asyncio
async def test_real_course_service_write_does_not_change_legacy_progress_or_tables() -> None:
    engine = create_async_engine(get_settings().database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    answer_id = None
    async with session_factory() as session:
        if await session.scalar(text("select to_regclass('public.course_answers')")) is None:
            pytest.skip("apply the P3 Course Answer migration before running this integration test")
        owner_id = await session.scalar(select(UserRow.id).order_by(UserRow.id).limit(1))
        if owner_id is None:
            pytest.skip("configured test database has no user fixture")
        before = await sqlalchemy_legacy_snapshot(session, owner_id)
        service = CourseAnswerService(
            repository=SQLCourseAnswerRepository(session),
            stt=FakeSpeechToTextService("Real repository isolation transcript."),
            tts=FakeTextToSpeechService(),
            audio=FakeCourseAudioStorage(),
        )
        try:
            answer = await service.submit_english(
                user_id=owner_id,
                course_id="course-11",
                question_id="course-11.core",
                idempotency_key=f"database-service-{uuid4()}",
                audio=b"database-integration-audio",
                content_type="audio/webm",
                duration_ms=1700,
            )
            answer_id = answer.answer.id
            assert answer.answer.status == "SAVED"
            assert await sqlalchemy_legacy_snapshot(session, owner_id) == before
        finally:
            if answer_id is not None:
                await session.execute(
                    delete(CourseAnswerRow).where(CourseAnswerRow.id == answer_id)
                )
                await session.commit()
    await engine.dispose()
