from typing import Protocol
from uuid import UUID

import httpx

from app.core.config import get_settings


class DocumentStorage(Protocol):
    async def store_resume(
        self, *, user_id: UUID, document_id: UUID, filename: str, content: bytes
    ) -> str: ...
    async def delete(self, *, path: str) -> None: ...


class FakeDocumentStorage:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.fail_deletes = False

    async def store_resume(
        self, *, user_id: UUID, document_id: UUID, filename: str, content: bytes
    ) -> str:
        safe_name = filename.replace("/", "_").replace("\\", "_")
        path = f"{user_id}/{document_id}/{safe_name}"
        self.objects[path] = content
        return path

    async def delete(self, *, path: str) -> None:
        if self.fail_deletes:
            raise RuntimeError("Document cleanup failed.")
        self.objects.pop(path, None)


class SupabaseDocumentStorage:
    def __init__(self, *, supabase_url: str, service_role_key: str) -> None:
        self._url = supabase_url.rstrip("/")
        self._key = service_role_key

    async def store_resume(
        self, *, user_id: UUID, document_id: UUID, filename: str, content: bytes
    ) -> str:
        safe_name = filename.replace("/", "_").replace("\\", "_")
        path = f"{user_id}/{document_id}/{safe_name}"
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{self._url}/storage/v1/object/resumes/{path}",
                headers={
                    "apikey": self._key,
                    "Authorization": f"Bearer {self._key}",
                    "Content-Type": "application/pdf",
                    "x-upsert": "false",
                },
                content=content,
            )
            response.raise_for_status()
        return path

    async def delete(self, *, path: str) -> None:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.delete(
                f"{self._url}/storage/v1/object/resumes/{path}",
                headers={"apikey": self._key, "Authorization": f"Bearer {self._key}"},
            )
        if response.status_code not in {200, 404}:
            response.raise_for_status()


def build_document_storage() -> DocumentStorage:
    settings = get_settings()
    if settings.document_storage_provider == "supabase":
        if not settings.supabase_service_role_key:
            raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY is required for document storage.")
        return SupabaseDocumentStorage(
            supabase_url=settings.supabase_url,
            service_role_key=settings.supabase_service_role_key,
        )
    return FakeDocumentStorage()
