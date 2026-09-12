import os
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.about_me.repository import SQLAboutMeRepository
from app.core.config import get_settings
from app.course.context import CourseContextBuilder
from app.course.repository import SQLCourseAnswerRepository
from app.course.support_provider import FakeCourseSupportProvider
from app.course.support_service import CourseSupportService

LEGACY_TABLES = (
    "sessions",
    "attempts",
    "expressions",
    "expression_attempts",
    "retrieval_opportunities",
)


async def legacy_snapshot(session, user_id):
    progress = (
        await session.execute(
            text(
                "select current_day, current_phase, xp, current_streak "
                "from public.users where id = :user_id"
            ),
            {"user_id": user_id},
        )
    ).one()
    counts = {
        table: await session.scalar(
            text(f"select count(*) from public.{table} where user_id = :user_id"),
            {"user_id": user_id},
        )
        for table in LEGACY_TABLES
    }
    return tuple(progress), counts


@pytest.mark.skipif(
    os.getenv("RUN_COURSE_CORE_DB_INTEGRATION") != "1",
    reason="set RUN_COURSE_CORE_DB_INTEGRATION=1 to use the configured PostgreSQL test database",
)
@pytest.mark.asyncio
async def test_real_feedback_retry_is_owned_idempotent_and_legacy_isolated() -> None:
    engine = create_async_engine(get_settings().database_url)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    answer_id = uuid4()
    async with factory() as session:
        user_ids = (
            await session.scalars(text("select id from public.users order by id limit 2"))
        ).all()
        if len(user_ids) < 2:
            pytest.skip("configured test database needs two user fixtures")
        user_id, other_user_id = user_ids
        before = await legacy_snapshot(session, user_id)
        try:
            await session.execute(
                text(
                    "insert into public.course_answers "
                    "(id, user_id, course_id, question_id, answer_language, status, "
                    "idempotency_key, saved_at, saved_sequence) values "
                    "(:id, :user_id, 'course-11', 'course-11.core', 'ENGLISH', 'SAVED', "
                    ":key, now(), nextval('public.course_answer_saved_sequence'))"
                ),
                {"id": answer_id, "user_id": user_id, "key": f"p5-feedback-{uuid4()}"},
            )
            await session.execute(
                text(
                    "insert into public.course_transcripts "
                    "(answer_id, user_id, source_language, transcript, stt_provider) "
                    "values (:id, :user_id, 'ENGLISH', :transcript, 'test')"
                ),
                {
                    "id": answer_id,
                    "user_id": user_id,
                    "transcript": "I led the migration and chose a phased rollout.",
                },
            )
            await session.commit()
            answers = SQLCourseAnswerRepository(session)
            service = CourseSupportService(
                repository=answers,
                context_builder=CourseContextBuilder(
                    about_me=SQLAboutMeRepository(session), answers=answers
                ),
                provider=FakeCourseSupportProvider(),
            )

            assert await service.hints(
                user_id=user_id, course_id="course-11", question_id="course-11.core"
            )
            assert await service.expression_materials(
                user_id=user_id, course_id="course-11", question_id="course-11.core"
            )
            assert await service.reference_answer(
                user_id=user_id, course_id="course-11", question_id="course-11.core"
            )

            first = await service.generate_for_answer(user_id=user_id, answer_id=answer_id)
            second = await service.generate_for_answer(user_id=user_id, answer_id=answer_id)
            assert first.answer.status == second.answer.status == "SAVED"
            assert second.feedback is not None and second.feedback.status == "READY"
            assert (
                await session.scalar(
                    text("select count(*) from public.course_feedback where answer_id = :id"),
                    {"id": answer_id},
                )
                == 1
            )
            with pytest.raises(LookupError):
                await service.generate_for_answer(user_id=other_user_id, answer_id=answer_id)
            assert await legacy_snapshot(session, user_id) == before
        finally:
            await session.execute(
                text("delete from public.course_answers where id = :id"), {"id": answer_id}
            )
            await session.commit()
    await engine.dispose()
