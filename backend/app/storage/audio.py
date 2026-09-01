from typing import Protocol
from uuid import UUID

import httpx


class AudioStorage(Protocol):
    async def store(
        self,
        *,
        user_id: UUID,
        session_id: UUID,
        attempt_id: UUID,
        content: bytes,
        content_type: str,
    ) -> str: ...
    async def load(self, *, path: str) -> bytes: ...


class FakeAudioStorage:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    async def store(
        self,
        *,
        user_id: UUID,
        session_id: UUID,
        attempt_id: UUID,
        content: bytes,
        content_type: str,
    ) -> str:
        del content_type
        path = f"{user_id}/{session_id}/{attempt_id}"
        self.objects[path] = content
        return path

    async def load(self, *, path: str) -> bytes:
        try:
            return self.objects[path]
        except KeyError as error:
            raise LookupError("Stored learner audio was not found.") from error


class SupabaseAudioStorage:
    def __init__(self, *, supabase_url: str, service_role_key: str) -> None:
        self._url = supabase_url.rstrip("/")
        self._headers = {"Authorization": f"Bearer {service_role_key}", "apikey": service_role_key}

    async def store(
        self,
        *,
        user_id: UUID,
        session_id: UUID,
        attempt_id: UUID,
        content: bytes,
        content_type: str,
    ) -> str:
        path = f"{user_id}/{session_id}/{attempt_id}"
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{self._url}/storage/v1/object/learner-audio/{path}",
                content=content,
                headers={**self._headers, "Content-Type": content_type, "x-upsert": "true"},
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
