import os
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.about_me.entities import MemoryCitation, MemoryDecision
from app.about_me.repository import SQLAboutMeRepository
from app.core.config import get_settings
from app.course.repository import SQLCourseAnswerRepository

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
async def test_real_memory_decisions_source_cleanup_and_legacy_isolation() -> None:
    engine = create_async_engine(get_settings().database_url)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    answer_ids = [uuid4(), uuid4()]
    memory_ids = []
    async with factory() as session:
        if await session.scalar(text("select to_regclass('public.memory_items')")) is None:
            pytest.skip("apply the P4 About Me migration before running this integration test")
        user_id = await session.scalar(text("select id from public.users order by id limit 1"))
        if user_id is None:
            pytest.skip("configured test database has no user fixture")
        before = await legacy_snapshot(session, user_id)
        try:
            for index, answer_id in enumerate(answer_ids, start=1):
                await session.execute(
                    text(
                        "insert into public.course_answers "
                        "(id, user_id, course_id, question_id, answer_language, status, "
                        "idempotency_key, saved_at, saved_sequence) values "
                        "(:id, :user_id, 'course-11', 'course-11.core', 'ENGLISH', 'SAVED', "
                        ":key, now(), nextval('public.course_answer_saved_sequence'))"
                    ),
                    {"id": answer_id, "user_id": user_id, "key": f"p4-memory-{uuid4()}"},
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
                        "transcript": f"I led verified project {index}.",
                    },
                )
            await session.commit()
            repository = SQLAboutMeRepository(session)

            created = await repository.apply_memory_decision(
                user_id,
                MemoryDecision(
                    action="CREATE",
                    candidate_content="Led a verified project.",
                    target_memory_ids=[],
                    source_citations=[
                        MemoryCitation(
                            source_type="COURSE_ANSWER",
                            source_id=answer_ids[0],
                            source_excerpt="led verified project 1",
                            source_field_path="transcript",
                        )
                    ],
                ),
            )
            assert created is not None
            memory_ids.append(created.id)
            updated = await repository.apply_memory_decision(
                user_id,
                MemoryDecision(
                    action="UPDATE",
                    candidate_content="Led two verified projects.",
                    target_memory_ids=[created.id],
                    source_citations=[
                        MemoryCitation(
                            source_type="COURSE_ANSWER",
                            source_id=answer_ids[1],
                            source_excerpt="verified project 2",
                            source_field_path="transcript",
                        )
                    ],
                ),
            )
            second = await repository.apply_memory_decision(
                user_id,
                MemoryDecision(
                    action="CREATE",
                    candidate_content="Project evidence.",
                    target_memory_ids=[],
                    source_citations=[
                        MemoryCitation(
                            source_type="COURSE_ANSWER",
                            source_id=answer_ids[0],
                            source_excerpt="verified project 1",
                        )
                    ],
                ),
            )
            assert updated is not None and second is not None
            memory_ids.append(second.id)
            merged = await repository.apply_memory_decision(
                user_id,
                MemoryDecision(
                    action="MERGE",
                    candidate_content="Led two verified projects.",
                    target_memory_ids=[created.id, second.id],
                    source_citations=[
                        MemoryCitation(
                            source_type="COURSE_ANSWER",
                            source_id=answer_ids[1],
                            source_excerpt="led verified project 2",
                        )
                    ],
                ),
            )
            assert merged is not None and len(merged.sources) >= 2
            assert (
                await repository.apply_memory_decision(
                    user_id,
                    MemoryDecision(
                        action="IGNORE",
                        candidate_content=None,
                        target_memory_ids=[],
                        source_citations=[],
                    ),
                )
                is None
            )
            with pytest.raises(ValueError, match="owned source"):
                await repository.apply_memory_decision(
                    user_id,
                    MemoryDecision(
                        action="CREATE",
                        candidate_content="Fabricated.",
                        target_memory_ids=[],
                        source_citations=[
                            MemoryCitation(
                                source_type="COURSE_ANSWER",
                                source_id=answer_ids[0],
                                source_excerpt="not in the transcript",
                            )
                        ],
                    ),
                )

            course_repository = SQLCourseAnswerRepository(session)
            await course_repository.delete(user_id, answer_ids[0])
            after_one = await repository.snapshot(user_id)
            assert any(item.id == merged.id for item in after_one.memories)
            await course_repository.delete(user_id, answer_ids[1])
            after_two = await repository.snapshot(user_id)
            assert all(item.id != merged.id for item in after_two.memories)
            assert await legacy_snapshot(session, user_id) == before
        finally:
            await session.execute(
                text("delete from public.memory_items where id = any(:ids)"),
                {"ids": memory_ids},
            )
            await session.execute(
                text("delete from public.course_answers where id = any(:ids)"),
                {"ids": answer_ids},
            )
            await session.commit()
    await engine.dispose()


@pytest.mark.skipif(
    os.getenv("RUN_COURSE_CORE_DB_INTEGRATION") != "1",
    reason="set RUN_COURSE_CORE_DB_INTEGRATION=1 to use the configured PostgreSQL test database",
)
@pytest.mark.asyncio
async def test_about_me_rls_isolates_two_users_and_forbids_direct_writes() -> None:
    engine = create_async_engine(get_settings().database_url)
    async with engine.connect() as sql_connection:
        raw = await sql_connection.get_raw_connection()
        connection = raw.driver_connection
        users = await connection.fetch("select id from public.users order by id limit 2")
        if len(users) < 2:
            pytest.skip("configured test database needs two user fixtures")
        owner_id, other_id = users[0]["id"], users[1]["id"]
        transaction = connection.transaction()
        await transaction.start()
        try:
            role_id = uuid4()
            await connection.execute(
                "insert into public.target_roles (id, user_id, role_name) values ($1, $2, $3)",
                role_id,
                owner_id,
                f"P4 RLS {role_id}",
            )
            await connection.execute("set local role authenticated")
            await connection.execute(
                "select set_config('request.jwt.claim.sub', $1, true)", str(owner_id)
            )
            assert (
                await connection.fetchval(
                    "select count(*) from public.target_roles where id = $1", role_id
                )
                == 1
            )
            assert not await connection.fetchval(
                "select has_table_privilege(current_user, 'public.target_roles', 'INSERT')"
            )
            await connection.execute(
                "select set_config('request.jwt.claim.sub', $1, true)", str(other_id)
            )
            assert (
                await connection.fetchval(
                    "select count(*) from public.target_roles where id = $1", role_id
                )
                == 0
            )
        finally:
            await transaction.rollback()
    await engine.dispose()


@pytest.mark.skipif(
    os.getenv("RUN_COURSE_CORE_DB_INTEGRATION") != "1",
    reason="set RUN_COURSE_CORE_DB_INTEGRATION=1 to use the configured PostgreSQL test database",
)
@pytest.mark.asyncio
async def test_profile_resume_and_user_input_sources_are_exact_and_owned() -> None:
    engine = create_async_engine(get_settings().database_url)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    role_id, document_id = uuid4(), uuid4()
    memory_ids = []
    async with factory() as session:
        user_id = await session.scalar(
            text(
                "select u.id from public.users u left join public.about_me_profiles p "
                "on p.user_id = u.id where p.user_id is null order by u.id limit 1"
            )
        )
        if user_id is None:
            pytest.skip("configured test database has no user without P4 profile data")
        before = await legacy_snapshot(session, user_id)
        try:
            await session.execute(
                text(
                    "insert into public.about_me_profiles (user_id, supplemental_facts) "
                    "values (:u, '[\"Synthetic supplemental fact.\"]'::jsonb)"
                ),
                {"u": user_id},
            )
            await session.execute(
                text(
                    "insert into public.target_roles (id, user_id, role_name) "
                    "values (:id, :u, 'Synthetic Product Role')"
                ),
                {"id": role_id, "u": user_id},
            )
            await session.execute(
                text(
                    "insert into public.source_documents "
                    "(id, user_id, source_type, filename, storage_path, raw_text, parse_status) "
                    "values (:id, :u, 'resume_pdf', 'synthetic.pdf', 'synthetic/path.pdf', "
                    "'Synthetic resume project evidence.', 'ready')"
                ),
                {"id": document_id, "u": user_id},
            )
            await session.commit()
            repository = SQLAboutMeRepository(session)
            citations = (
                MemoryCitation(
                    source_type="PROFILE",
                    source_id=role_id,
                    source_excerpt="Product Role",
                    source_field_path="target_roles",
                ),
                MemoryCitation(
                    source_type="SOURCE_DOCUMENT",
                    source_id=document_id,
                    source_excerpt="resume project evidence",
                ),
                MemoryCitation(
                    source_type="USER_INPUT",
                    source_id=user_id,
                    source_excerpt="supplemental fact",
                    source_field_path="supplemental_facts",
                ),
            )
            for index, citation in enumerate(citations):
                memory = await repository.apply_memory_decision(
                    user_id,
                    MemoryDecision(
                        action="CREATE",
                        candidate_content=f"Validated synthetic memory {index}.",
                        target_memory_ids=[],
                        source_citations=[citation],
                    ),
                )
                assert memory is not None
                memory_ids.append(memory.id)
            with pytest.raises(ValueError, match="owned source"):
                await repository.apply_memory_decision(
                    user_id,
                    MemoryDecision(
                        action="CREATE",
                        candidate_content="Unowned source.",
                        target_memory_ids=[],
                        source_citations=[
                            MemoryCitation(
                                source_type="SOURCE_DOCUMENT",
                                source_id=uuid4(),
                                source_excerpt="anything",
                            )
                        ],
                    ),
                )
            pending = await repository.delete_resume(user_id, document_id)
            assert pending is not None and pending.storage_path == "synthetic/path.pdf"
            after_resume_delete = await repository.snapshot(user_id)
            assert all(item.id != memory_ids[1] for item in after_resume_delete.memories)
            await repository.mark_document_cleanup_complete(user_id, document_id)
            assert await legacy_snapshot(session, user_id) == before
        finally:
            await session.execute(
                text("delete from public.memory_sources where user_id = :u"), {"u": user_id}
            )
            await session.execute(
                text("delete from public.memory_items where user_id = :u"), {"u": user_id}
            )
            await session.execute(
                text("delete from public.source_documents where id = :id"), {"id": document_id}
            )
            await session.execute(
                text("delete from public.target_roles where id = :id"), {"id": role_id}
            )
            await session.execute(
                text("delete from public.about_me_profiles where user_id = :u"), {"u": user_id}
            )
            await session.commit()
    await engine.dispose()


@pytest.mark.skipif(
    os.getenv("RUN_COURSE_CORE_DB_INTEGRATION") != "1",
    reason="set RUN_COURSE_CORE_DB_INTEGRATION=1 to use the configured PostgreSQL test database",
)
@pytest.mark.asyncio
async def test_database_rejects_a_source_less_memory_at_commit() -> None:
    engine = create_async_engine(get_settings().database_url)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        user_id = await session.scalar(text("select id from public.users order by id limit 1"))
        if user_id is None:
            pytest.skip("configured test database has no user fixture")
        await session.execute(
            text(
                "insert into public.memory_items "
                "(id, user_id, content, normalized_content, extractor_prompt_version) "
                "values (:id, :u, 'No source.', 'no source.', 'memory_decision_v1')"
            ),
            {"id": uuid4(), "u": user_id},
        )
        with pytest.raises(DBAPIError, match="must have at least one source"):
            await session.commit()
        await session.rollback()
    await engine.dispose()
