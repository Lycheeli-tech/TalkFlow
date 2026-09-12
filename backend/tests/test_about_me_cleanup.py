from uuid import uuid4

import pytest

from app.about_me.cleanup import cleanup_about_me_documents_batch
from app.about_me.entities import PendingDocumentCleanup
from app.storage.documents import FakeDocumentStorage


class CleanupRepository:
    def __init__(self, item: PendingDocumentCleanup) -> None:
        self.item = item
        self.failed = 0
        self.complete = 0

    async def list_document_cleanup_jobs(self, limit: int):
        del limit
        return [] if self.complete else [self.item]

    async def mark_document_cleanup_complete(self, user_id, document_id):
        assert (user_id, document_id) == (self.item.user_id, self.item.document_id)
        self.complete += 1

    async def mark_document_cleanup_failed(self, user_id, document_id):
        assert (user_id, document_id) == (self.item.user_id, self.item.document_id)
        self.failed += 1


@pytest.mark.asyncio
async def test_resume_cleanup_failure_remains_retryable_and_then_completes() -> None:
    item = PendingDocumentCleanup(
        document_id=uuid4(), user_id=uuid4(), storage_path="owned/resume.pdf"
    )
    repository = CleanupRepository(item)
    storage = FakeDocumentStorage()
    storage.objects[item.storage_path] = b"pdf"
    storage.fail_deletes = True

    assert await cleanup_about_me_documents_batch(repository=repository, storage=storage) == 0
    assert repository.failed == 1
    assert repository.complete == 0

    storage.fail_deletes = False
    assert await cleanup_about_me_documents_batch(repository=repository, storage=storage) == 1
    assert repository.complete == 1
    assert storage.objects == {}
