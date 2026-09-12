from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_memory_repository,
    get_retrieval_opportunity_repository,
    get_verification_service,
)
from app.api.v1.memory import list_due_retrieval, resolve_retrieval
from app.repositories.memory import InMemoryMemoryRepository
from app.repositories.retrieval import InMemoryRetrievalOpportunityRepository
from app.schemas import AuthenticatedUser, Expression, RetrievalResult
from app.services.verification import VerificationService


class StubUnitOfWork:
    def __init__(self) -> None:
        self.calls: list[tuple[UUID, UUID, UUID]] = []

    async def resolve(
        self, *, user_id: UUID, opportunity_id: UUID, attempt_id: UUID
    ) -> RetrievalResult:
        self.calls.append((user_id, opportunity_id, attempt_id))
        return RetrievalResult(
            opportunity_id=opportunity_id,
            recorded=True,
            expression_status="TRANSFERRED",
        )


def test_due_retrieval_api_is_registered() -> None:
    assert list_due_retrieval.__name__ == "list_due_retrieval"
    assert resolve_retrieval.__name__ == "resolve_retrieval"


def test_due_opportunity_response_does_not_expose_hidden_expression(
    legacy_client: TestClient, override_current_user
) -> None:
    now, user_id, session_id = datetime.now(UTC), uuid4(), uuid4()
    target = Expression(
        id=uuid4(),
        user_id=user_id,
        text="highly transferable",
        meaning="useful in another context",
        source_type="CURRICULUM",
        status="RECALLED",
        next_review_at=now - timedelta(days=1),
        created_at=now,
        updated_at=now,
    )
    memory = InMemoryMemoryRepository()
    memory.expressions[target.id] = target
    opportunities = InMemoryRetrievalOpportunityRepository()
    override_current_user(AuthenticatedUser(id=user_id, email="learner@example.com"))
    application = legacy_client.app
    application.dependency_overrides[get_memory_repository] = lambda: memory
    application.dependency_overrides[get_retrieval_opportunity_repository] = lambda: opportunities

    response = legacy_client.get(
        "/api/v1/memory/retrieval/due",
        params={
            "session_id": str(session_id),
            "question_family": "RELEVANT_EXPERIENCE",
            "question_text": "How does your background prepare you for this role?",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["question_text"] == "How does your background prepare you for this role?"
    assert "expression_id" not in body
    assert target.text not in response.text


def test_resolve_api_accepts_only_attempt_identity_and_uses_authenticated_user(
    legacy_client: TestClient, override_current_user
) -> None:
    user_id, opportunity_id, attempt_id = uuid4(), uuid4(), uuid4()
    override_current_user(AuthenticatedUser(id=user_id, email="learner@example.com"))
    unit_of_work = StubUnitOfWork()
    legacy_client.app.dependency_overrides[get_verification_service] = lambda: VerificationService(
        unit_of_work
    )

    forged = legacy_client.post(
        f"/api/v1/memory/retrieval/{opportunity_id}/resolve",
        json={"attempt_id": str(attempt_id), "usage_correct": True},
    )
    assert forged.status_code == 422
    assert unit_of_work.calls == []

    response = legacy_client.post(
        f"/api/v1/memory/retrieval/{opportunity_id}/resolve",
        json={"attempt_id": str(attempt_id)},
    )
    assert response.status_code == 200
    assert response.json() == {
        "opportunity_id": str(opportunity_id),
        "opportunity_status": "CONSUMED",
        "recorded": True,
        "expression_status": "TRANSFERRED",
        "next_review_at": None,
    }
    assert unit_of_work.calls == [(user_id, opportunity_id, attempt_id)]
