import asyncio
import logging
from contextlib import suppress
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select, update

from app.db.session import get_session_factory
from app.practice_v2.repository import PracticeCleanupRow, SQLPracticeRepository

logger = logging.getLogger(__name__)


async def cleanup_once(session, audio, *, now=None, owner=None):
    now = now or datetime.now(UTC)
    await SQLPracticeRepository(session).expire(now, owner)
    statement = (
        select(PracticeCleanupRow)
        .where(PracticeCleanupRow.next_attempt_at <= now)
        .execution_options(populate_existing=True)
    )
    if owner is not None:
        statement = statement.where(PracticeCleanupRow.user_id == owner)
    jobs = (await session.scalars(statement.limit(50))).all()
    for job in jobs:
        path, attempts, scheduled = job.storage_path, job.attempts, job.next_attempt_at
        try:
            await audio.delete(path)
            await session.execute(
                delete(PracticeCleanupRow).where(
                    PracticeCleanupRow.storage_path == path,
                    PracticeCleanupRow.attempts == attempts,
                    PracticeCleanupRow.next_attempt_at == scheduled,
                )
            )
        except Exception:
            await session.execute(
                update(PracticeCleanupRow)
                .where(
                    PracticeCleanupRow.storage_path == path,
                    PracticeCleanupRow.attempts == attempts,
                    PracticeCleanupRow.next_attempt_at == scheduled,
                )
                .values(
                    attempts=attempts + 1,
                    next_attempt_at=now
                    + timedelta(seconds=min(86400, 60 * 2 ** min(attempts, 11))),
                )
            )
        await session.commit()


async def run_practice_cleanup_loop():
    from app.api.practice_dependencies import get_practice_audio

    while True:
        await asyncio.sleep(60)
        try:
            async with get_session_factory()() as session:
                await cleanup_once(session, get_practice_audio())
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.warning("practice_cleanup_unavailable")


async def stop_practice_cleanup(task):
    task.cancel()
    with suppress(asyncio.CancelledError):
        await task
