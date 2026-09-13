import json

import httpx
import pytest

from app.course.storage import SupabaseCourseAudioStorage


@pytest.mark.asyncio
async def test_course_audio_delete_uses_exact_object_prefix_and_is_idempotent(monkeypatch):
    requests = []
    real_client = httpx.AsyncClient

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json=[])

    def client_factory(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        return real_client(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", client_factory)
    storage = SupabaseCourseAudioStorage(
        supabase_url="https://test.supabase.co", service_role_key="test-key"
    )
    for _ in range(2):
        await storage.delete(path="owner/course-answers/answer")
    assert len(requests) == 2
    for request in requests:
        assert request.method == "DELETE"
        assert request.url.path == "/storage/v1/object/learner-audio"
        assert json.loads(request.content) == {"prefixes": ["owner/course-answers/answer"]}
