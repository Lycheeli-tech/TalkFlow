from uuid import uuid4

import httpx
import pytest

from app.storage.documents import DocumentStorageError, FakeDocumentStorage, SupabaseDocumentStorage


@pytest.mark.asyncio
@pytest.mark.parametrize("filename", ["简历 测试.pdf", "résumé.pdf", "../private/简历.pdf"])
async def test_private_object_key_does_not_depend_on_display_filename(monkeypatch, filename):
    owner, document = uuid4(), uuid4()
    expected = f"{owner}/{document}/resume.pdf"
    requests = []
    real_client = httpx.AsyncClient

    def handle(request):
        requests.append(request)
        return httpx.Response(200, json={"Key": expected})

    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: real_client(transport=httpx.MockTransport(handle), **kwargs),
    )
    storage = SupabaseDocumentStorage(
        supabase_url="https://storage.example.test", service_role_key="test"
    )
    content = b"%PDF synthetic"
    assert (
        await storage.store_resume(
            user_id=owner, document_id=document, filename=filename, content=content
        )
        == expected
    )
    assert requests[0].url.path == "/storage/v1/object/resumes/" + expected
    assert requests[0].content == content
    assert requests[0].headers["x-upsert"] == "false"
    fake = FakeDocumentStorage()
    assert (
        await fake.store_resume(
            user_id=owner, document_id=document, filename=filename, content=content
        )
        == expected
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("network_failure", [False, True])
async def test_upload_failure_is_safe_and_actionable(monkeypatch, network_failure):
    real_client = httpx.AsyncClient

    def handle(request):
        if network_failure:
            raise httpx.ConnectError("private provider details", request=request)
        return httpx.Response(400, json={"error": "private provider details"})

    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: real_client(transport=httpx.MockTransport(handle), **kwargs),
    )
    storage = SupabaseDocumentStorage(
        supabase_url="https://storage.example.test", service_role_key="test"
    )
    with pytest.raises(
        DocumentStorageError, match="^Resume upload unavailable. Please try again.$"
    ):
        await storage.store_resume(
            user_id=uuid4(), document_id=uuid4(), filename="简历.pdf", content=b"%PDF synthetic"
        )
