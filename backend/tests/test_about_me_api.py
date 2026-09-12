from datetime import UTC, datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from app.about_me.entities import AboutMeSnapshot, MemoryItem, ResumeDocument, TargetRole
from app.api.about_me_dependencies import get_about_me_service
from app.main import app
from app.schemas import AuthenticatedUser


class StubAboutMeService:
    def __init__(self, user_id):
        self.user_id = user_id
        self.roles: list[TargetRole] = []
        self.resumes: list[ResumeDocument] = []
        self.memories: list[MemoryItem] = []
        self.facts: list[str] = []

    async def get(self, user_id):
        assert user_id == self.user_id
        return self.snapshot()

    async def update_facts(self, user_id, facts):
        assert user_id == self.user_id
        self.facts = facts
        return self.snapshot()

    async def add_target_role(self, user_id, role_name):
        role = TargetRole(
            id=uuid4(), user_id=user_id, role_name=role_name, created_at=datetime.now(UTC)
        )
        self.roles.append(role)
        return role

    async def delete_target_role(self, user_id, role_id):
        before = len(self.roles)
        self.roles = [
            item for item in self.roles if not (item.user_id == user_id and item.id == role_id)
        ]
        if len(self.roles) == before:
            raise LookupError("About Me item was not found.")

    async def add_resume(self, *, user_id, filename, content_type, content):
        assert content_type == "application/pdf"
        document = ResumeDocument(
            id=uuid4(),
            user_id=user_id,
            filename=filename,
            raw_text=f"private:{len(content)}",
            parse_status="ready",
            created_at=datetime.now(UTC),
        )
        self.resumes.append(document)
        return document

    async def delete_resume(self, user_id, document_id):
        before = len(self.resumes)
        self.resumes = [
            item
            for item in self.resumes
            if not (item.user_id == user_id and item.id == document_id)
        ]
        if len(self.resumes) == before:
            raise LookupError("About Me item was not found.")

    async def delete_memory(self, user_id, memory_id):
        del user_id, memory_id
        raise LookupError("About Me item was not found.")

    def snapshot(self):
        return AboutMeSnapshot(
            supplemental_facts=self.facts,
            target_roles=self.roles,
            resumes=self.resumes,
            memories=self.memories,
        )


def configure(client: TestClient, override_current_user):
    user = AuthenticatedUser(id=uuid4(), email="about@example.test")
    override_current_user(user)
    service = StubAboutMeService(user.id)
    app.dependency_overrides[get_about_me_service] = lambda: service
    return service


def test_about_me_is_optional_and_requires_authentication(client: TestClient) -> None:
    assert client.get("/api/v1/about-me").status_code == 401


def test_about_me_roles_facts_resumes_and_non_enumerating_delete(
    client: TestClient, override_current_user
) -> None:
    service = configure(client, override_current_user)
    empty = client.get("/api/v1/about-me")
    assert empty.status_code == 200
    assert empty.json() == {
        "supplemental_facts": [],
        "target_roles": [],
        "resumes": [],
        "memories": [],
    }

    role = client.post("/api/v1/about-me/target-roles", json={"role_name": "Product Manager"})
    assert role.status_code == 201
    assert "user_id" not in role.json()
    assert role.json()["role_name"] == "Product Manager"

    facts = client.patch("/api/v1/about-me", json={"supplemental_facts": ["Led a migration."]})
    assert facts.status_code == 200
    assert facts.json()["supplemental_facts"] == ["Led a migration."]

    resume = client.post(
        "/api/v1/about-me/resumes",
        files={"resume": ("resume.pdf", b"%PDF fixture", "application/pdf")},
    )
    assert resume.status_code == 201
    assert "raw_text" not in resume.json()
    assert len(service.resumes) == 1

    assert client.delete(f"/api/v1/about-me/target-roles/{role.json()['id']}").status_code == 200
    assert client.delete(f"/api/v1/about-me/resumes/{resume.json()['id']}").status_code == 200
    assert client.delete(f"/api/v1/about-me/memories/{uuid4()}").status_code == 404
