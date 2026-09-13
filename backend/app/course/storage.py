from typing import Protocol
from uuid import UUID

import httpx

from app.core.config import get_settings


class CourseAudioStorage(Protocol):
    async def store(
        self, *, user_id: UUID, answer_id: UUID, content: bytes, content_type: str
    ) -> str: ...
    async def load(self, *, path: str) -> bytes: ...
    async def delete(self, *, path: str) -> None: ...


class FakeCourseAudioStorage:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.fail_deletes = False

    async def store(
        self, *, user_id: UUID, answer_id: UUID, content: bytes, content_type: str
    ) -> str:
        del content_type
        path = f"{user_id}/course-answers/{answer_id}"
        self.objects[path] = content
        return path

    async def load(self, *, path: str) -> bytes:
        try:
            return self.objects[path]
        except KeyError as error:
            raise LookupError("Stored Course Answer audio was not found.") from error

    async def delete(self, *, path: str) -> None:
        if self.fail_deletes:
            raise RuntimeError("Course audio cleanup failed.")
        self.objects.pop(path, None)


class SupabaseCourseAudioStorage:
    def __init__(self, *, supabase_url: str, service_role_key: str) -> None:
        self._url = supabase_url.rstrip("/")
        self._headers = {"Authorization": f"Bearer {service_role_key}", "apikey": service_role_key}

    async def store(
        self, *, user_id: UUID, answer_id: UUID, content: bytes, content_type: str
    ) -> str:
        path = f"{user_id}/course-answers/{answer_id}"
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{self._url}/storage/v1/object/learner-audio/{path}",
                content=content,
                headers={**self._headers, "Content-Type": content_type, "x-upsert": "false"},
            )
        response.raise_for_status()
        return path

    async def load(self, *, path: str) -> bytes:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{self._url}/storage/v1/object/learner-audio/{path}", headers=self._headers
            )
        response.raise_for_status()
        return response.content

    async def delete(self, *, path: str) -> None:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.request(
                "DELETE",
                f"{self._url}/storage/v1/object/learner-audio",
                headers=self._headers,
                json={"prefixes": [path]},
            )
        if response.status_code not in {200, 404}:
            response.raise_for_status()


def build_course_audio_storage() -> CourseAudioStorage:
    settings = get_settings()
    if settings.audio_storage_provider == "supabase":
        if not settings.supabase_service_role_key:
            raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY is required for Course audio storage.")
        return SupabaseCourseAudioStorage(
            supabase_url=settings.supabase_url,
            service_role_key=settings.supabase_service_role_key,
        )
    return FakeCourseAudioStorage()
