from typing import Protocol
from uuid import UUID

import httpx


class DocumentStorage(Protocol):
    async def store_resume(
        self, *, user_id: UUID, document_id: UUID, filename: str, content: bytes
    ) -> str: ...


class FakeDocumentStorage:
    async def store_resume(
        self, *, user_id: UUID, document_id: UUID, filename: str, content: bytes
    ) -> str:
        del content
        safe_name = filename.replace("/", "_").replace("\\", "_")
        return f"{user_id}/{document_id}/{safe_name}"


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
