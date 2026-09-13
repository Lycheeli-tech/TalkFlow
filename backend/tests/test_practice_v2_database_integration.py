import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.ai.fakes import FakeSpeechToTextService, FakeTextToSpeechService
from app.core.config import get_settings
from app.practice_v2.answer_service import PracticeService
from app.practice_v2.cleanup import cleanup_once
from app.practice_v2.feedback_service import FakePracticeFeedbackProvider
from app.practice_v2.repository import PracticeCleanupRow, SQLPracticeRepository
from app.practice_v2.storage import PracticeAudioStorage

MIGRATION = (
    Path(__file__).resolve().parents[2] / "supabase/migrations/202609130021_practice_v2_runs.sql"
)


async def protected_snapshot(session):
    users = (
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
            "course_answers",
            "course_transcripts",
            "course_feedback",
            "memory_items",
            "memory_sources",
        )
    ]
    return users, counts


@pytest.mark.skipif(
    os.getenv("RUN_COURSE_CORE_DB_INTEGRATION") != "1", reason="opt-in real PostgreSQL"
)
@pytest.mark.asyncio
async def test_practice_migration_persistence_rls_cas_completion_expiry_and_cleanup_rollback():
    engine = create_async_engine(get_settings().database_url)
    try:
        async with engine.connect() as connection:
            transaction = await connection.begin()
            try:
                if not await connection.scalar(text("select to_regclass('public.practice_runs')")):
                    raw = await connection.get_raw_connection()
                    await raw.driver_connection.execute(MIGRATION.read_text(encoding="utf-8"))
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
                        pytest.skip("needs two test users")
                    owner, other = owners
                    before = await protected_snapshot(session)
                    audio = PracticeAudioStorage()
                    audio.remote = False
                    repo = SQLPracticeRepository(session)
                    service = PracticeService(
                        repository=repo,
                        audio=audio,
                        stt=FakeSpeechToTextService("I tested an idea with my team."),
                        tts=FakeTextToSpeechService(),
                        feedback=FakePracticeFeedbackProvider(),
                    )
                    run = await service.create(owner, 3, "p8-database-run", seed=23)
                    assert (await service.create(owner, 3, "p8-database-run")).id == run.id
                    assert await repo.get(other, run.id) is None
                    run = await service.submit(
                        owner,
                        run.id,
                        run.question_ids[0],
                        "p8-database-answer",
                        b"synthetic-contract",
                        "audio/webm",
                        1300,
                    )
                    attempt = run.answers[0]
                    assert attempt.status == "SAVED"
                    assert (
                        await service.submit(
                            owner,
                            run.id,
                            run.question_ids[0],
                            "p8-database-answer",
                            b"retry",
                            "audio/webm",
                            1300,
                        )
                    ).answers[0].id == attempt.id
                    old = await repo.get(owner, run.id)
                    await service.position(owner, run.id, 1, True, False)
                    with pytest.raises(ValueError):
                        await repo.save(old)
                    # Authenticate as the other owner: no leakage, and direct writes denied.
                    await session.execute(text("set local role authenticated"))
                    await session.execute(
                        text("select set_config('request.jwt.claim.sub',:owner,true)"),
                        {"owner": str(other)},
                    )
                    assert (
                        await session.scalar(
                            text("select count(*) from public.practice_runs where id=:id"),
                            {"id": run.id},
                        )
                        == 0
                    )
                    assert not await session.scalar(
                        text(
                            "select has_table_privilege("
                            "current_user,'public.practice_runs','INSERT')"
                        )
                    )
                    assert not await session.scalar(
                        text(
                            "select has_table_privilege("
                            "current_user,'public.practice_audio_cleanup_jobs','SELECT')"
                        )
                    )
                    await session.execute(text("reset role"))
                    run = await service.get(owner, run.id)
                    run.skipped = run.question_ids[1:]
                    await repo.save(run)
                    feedback = await service.complete(owner, run.id)
                    assert feedback.score == 95 and await repo.get(owner, run.id) is None
                    job = await session.scalar(
                        select(PracticeCleanupRow).where(
                            PracticeCleanupRow.storage_path == attempt.audio_path
                        )
                    )
                    assert job and job.user_id == owner

                    class BrokenAudio:
                        async def delete(self, path):
                            raise RuntimeError("synthetic outage")

                    now = datetime.now(UTC)
                    await cleanup_once(session, BrokenAudio(), now=now)
                    await session.refresh(job)
                    assert job.attempts == 1
                    await cleanup_once(session, audio, now=now + timedelta(seconds=61))
                    assert (
                        await session.scalar(
                            select(PracticeCleanupRow).where(
                                PracticeCleanupRow.storage_path == attempt.audio_path
                            )
                        )
                        is None
                    )
                    # A late upload can re-register the same path during an older cleanup.
                    await repo.queue_audio_cleanup(owner, attempt.audio_path)

                    class RequeueAudio:
                        async def delete(self, path):
                            await audio.delete(path)
                            await repo.queue_audio_cleanup(owner, path)

                    await cleanup_once(session, RequeueAudio(), owner=owner)
                    assert await session.scalar(
                        select(PracticeCleanupRow).where(
                            PracticeCleanupRow.storage_path == attempt.audio_path
                        )
                    )
                    await cleanup_once(session, audio, owner=owner)
                    assert (
                        await session.scalar(
                            select(PracticeCleanupRow).where(
                                PracticeCleanupRow.storage_path == attempt.audio_path
                            )
                        )
                        is None
                    )
                    expired = await service.create(owner, 5, "p8-expiry-run", seed=4)
                    expired.expires_at = now - timedelta(seconds=1)
                    await repo.save(expired)
                    # Mirror expiry in the immutable repository column for this controlled fixture.
                    await session.execute(
                        text("update public.practice_runs set expires_at=:expiry where id=:id"),
                        {"expiry": expired.expires_at, "id": expired.id},
                    )
                    await session.commit()
                    await session.execute(text("set local role authenticated"))
                    await session.execute(
                        text("select set_config('request.jwt.claim.sub',:owner,true)"),
                        {"owner": str(owner)},
                    )
                    assert (
                        await session.scalar(
                            text("select count(*) from public.practice_runs where id=:id"),
                            {"id": expired.id},
                        )
                        == 0
                    )
                    await session.execute(text("reset role"))
                    await cleanup_once(session, audio)
                    assert await repo.get(owner, expired.id) is None
                    assert await protected_snapshot(session) == before
            finally:
                await transaction.rollback()
    finally:
        await engine.dispose()
