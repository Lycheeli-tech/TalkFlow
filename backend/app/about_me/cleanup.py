import asyncio
import logging
from contextlib import suppress

from app.about_me.repository import AboutMeRepository, SQLAboutMeRepository
from app.core.config import get_settings
from app.db.session import get_session_factory
from app.storage.documents import DocumentStorage, build_document_storage

logger = logging.getLogger(__name__)


async def cleanup_about_me_documents_batch(
    *, repository: AboutMeRepository, storage: DocumentStorage, limit: int = 50
) -> int:
    pending = await repository.list_document_cleanup_jobs(limit)
    cleaned = 0
    for item in pending:
        try:
            await storage.delete(path=item.storage_path)
        except Exception:
            await repository.mark_document_cleanup_failed(item.user_id, item.document_id)
        else:
            await repository.mark_document_cleanup_complete(item.user_id, item.document_id)
            cleaned += 1
    return cleaned


async def run_about_me_document_cleanup_loop() -> None:
    interval = max(60, get_settings().course_audio_cleanup_interval_seconds)
    storage = build_document_storage()
    while True:
        await asyncio.sleep(interval)
        try:
            async with get_session_factory()() as session:
                await cleanup_about_me_documents_batch(
                    repository=SQLAboutMeRepository(session), storage=storage
                )
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("About Me document cleanup batch failed.")


async def stop_about_me_document_cleanup(task: asyncio.Task[None]) -> None:
    task.cancel()
    with suppress(asyncio.CancelledError):
        await task
