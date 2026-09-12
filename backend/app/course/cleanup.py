import asyncio
import logging
from contextlib import suppress
from datetime import UTC, datetime

from app.core.config import get_settings
from app.course.repository import CourseAnswerRepository, SQLCourseAnswerRepository
from app.course.storage import CourseAudioStorage, build_course_audio_storage
from app.db.session import get_session_factory

logger = logging.getLogger(__name__)


async def cleanup_course_audio_batch(
    *,
    repository: CourseAnswerRepository,
    audio: CourseAudioStorage,
    now: datetime | None = None,
    limit: int = 50,
) -> int:
    pending = await repository.list_pending_audio_cleanup(now=now or datetime.now(UTC), limit=limit)
    cleaned = 0
    for item in pending:
        try:
            await audio.delete(path=item.audio_path)
        except Exception:
            await repository.mark_cleanup_failed(item.user_id, item.answer_id)
        else:
            await repository.mark_cleanup_complete(item.user_id, item.answer_id)
            cleaned += 1
    return cleaned


async def run_course_audio_cleanup_loop() -> None:
    settings = get_settings()
    interval = max(60, settings.course_audio_cleanup_interval_seconds)
    audio = build_course_audio_storage()
    while True:
        await asyncio.sleep(interval)
        try:
            async with get_session_factory()() as session:
                await cleanup_course_audio_batch(
                    repository=SQLCourseAnswerRepository(session),
                    audio=audio,
                )
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Course audio cleanup batch failed.")


async def stop_course_audio_cleanup(task: asyncio.Task[None]) -> None:
    task.cancel()
    with suppress(asyncio.CancelledError):
        await task
