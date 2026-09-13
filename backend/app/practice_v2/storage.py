from uuid import UUID

import httpx

from app.core.config import get_settings


class PracticeAudioStorage:
    def __init__(self):
        settings = get_settings()
        self.remote = settings.audio_storage_provider == "supabase"
        self.url = settings.supabase_url.rstrip("/")
        key = settings.supabase_service_role_key
        self.headers = {"Authorization": f"Bearer {key}", "apikey": key or ""}
        self.objects: dict[str, bytes] = {}

    @staticmethod
    def path(owner: UUID, run_id: UUID, attempt_id: UUID) -> str:
        return f"{owner}/practice-v2/{run_id}/{attempt_id}"

    async def store(self, path: str, content: bytes, content_type: str):
        if not self.remote:
            self.objects[path] = content
            return
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{self.url}/storage/v1/object/learner-audio/{path}",
                content=content,
                headers={**self.headers, "Content-Type": content_type, "x-upsert": "false"},
            )
        if response.status_code == 409:
            await self.load(path)  # Recovery after upload succeeded but the response was lost.
            return
        response.raise_for_status()

    async def load(self, path: str) -> bytes:
        if not self.remote:
            return self.objects[path]
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{self.url}/storage/v1/object/learner-audio/{path}", headers=self.headers
            )
        response.raise_for_status()
        return response.content

    async def delete(self, path: str):
        if not self.remote:
            self.objects.pop(path, None)
            return
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.request(
                "DELETE",
                f"{self.url}/storage/v1/object/learner-audio",
                headers=self.headers,
                json={"prefixes": [path]},
            )
        if response.status_code not in (200, 404):
            response.raise_for_status()
