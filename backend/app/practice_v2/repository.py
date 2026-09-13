from copy import deepcopy
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

from sqlalchemy import DateTime, Integer, String, UniqueConstraint, delete, select, update
from sqlalchemy.dialects.postgresql import JSONB, insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.practice_v2.schemas import Run


class PracticeRunRow(Base):
    __tablename__ = "practice_runs"
    __table_args__ = (UniqueConstraint("user_id", "idempotency_key"), {"schema": "public"})
    id: Mapped[UUID] = mapped_column(primary_key=True)
    user_id: Mapped[UUID] = mapped_column()
    idempotency_key: Mapped[str] = mapped_column(String(128))
    revision: Mapped[int] = mapped_column(Integer)
    payload: Mapped[dict] = mapped_column(JSONB)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class PracticeCleanupRow(Base):
    __tablename__ = "practice_audio_cleanup_jobs"
    __table_args__ = {"schema": "public"}
    storage_path: Mapped[str] = mapped_column(primary_key=True)
    user_id: Mapped[UUID] = mapped_column()
    attempts: Mapped[int] = mapped_column(Integer)
    next_attempt_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class PracticeRepository(Protocol):
    async def get(self, owner: UUID, run_id: UUID) -> Run | None: ...
    async def current(self, owner: UUID) -> Run | None: ...
    async def find_key(self, owner: UUID, key: str) -> Run | None: ...
    async def create(self, run: Run) -> Run: ...
    async def save(self, run: Run) -> Run: ...
    async def remove(
        self, owner: UUID, run_id: UUID, expected_revision: int | None = None
    ) -> None: ...
    async def expire(self, now: datetime, owner: UUID | None = None) -> None: ...
    async def queue_audio_cleanup(self, owner: UUID, path: str) -> None: ...


class SQLPracticeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, owner, run_id):
        row = await self.session.scalar(
            select(PracticeRunRow).where(
                PracticeRunRow.id == run_id, PracticeRunRow.user_id == owner
            )
        )
        return Run.model_validate(row.payload) if row else None

    async def current(self, owner):
        rows = (
            await self.session.scalars(
                select(PracticeRunRow)
                .where(PracticeRunRow.user_id == owner)
                .order_by(PracticeRunRow.expires_at.desc())
            )
        ).all()
        return Run.model_validate(rows[0].payload) if rows else None

    async def find_key(self, owner, key):
        row = await self.session.scalar(
            select(PracticeRunRow).where(
                PracticeRunRow.user_id == owner, PracticeRunRow.idempotency_key == key
            )
        )
        return Run.model_validate(row.payload) if row else None

    async def create(self, run):
        from sqlalchemy.exc import IntegrityError

        self.session.add(
            PracticeRunRow(
                id=run.id,
                user_id=run.user_id,
                idempotency_key=run.idempotency_key,
                revision=0,
                payload=run.model_dump(mode="json"),
                expires_at=run.expires_at,
            )
        )
        try:
            await self.session.commit()
            return run
        except IntegrityError:
            await self.session.rollback()
            existing = await self.find_key(run.user_id, run.idempotency_key)
            if existing is None:
                raise
            return existing

    async def save(self, run):
        previous = run.revision
        run.revision += 1
        result = await self.session.execute(
            update(PracticeRunRow)
            .where(
                PracticeRunRow.id == run.id,
                PracticeRunRow.user_id == run.user_id,
                PracticeRunRow.revision == previous,
            )
            .values(payload=run.model_dump(mode="json"), revision=run.revision)
        )
        if result.rowcount != 1:
            await self.session.rollback()
            raise ValueError("Practice changed in another request. Reload before retrying.")
        await self.session.commit()
        return run

    async def remove(self, owner, run_id, expected_revision=None):
        statement = delete(PracticeRunRow).where(
            PracticeRunRow.id == run_id, PracticeRunRow.user_id == owner
        )
        if expected_revision is not None:
            statement = statement.where(PracticeRunRow.revision == expected_revision)
        result = await self.session.execute(statement)
        if expected_revision is not None and result.rowcount != 1:
            await self.session.rollback()
            raise ValueError("Practice changed before completion. Reload and retry.")
        await self.session.commit()  # BEFORE DELETE trigger durably queues every audio object.

    async def expire(self, now, owner=None):
        statement = delete(PracticeRunRow).where(PracticeRunRow.expires_at <= now)
        if owner is not None:
            statement = statement.where(PracticeRunRow.user_id == owner)
        await self.session.execute(statement)
        await self.session.commit()

    async def queue_audio_cleanup(self, owner, path):
        if not path.startswith(f"{owner}/practice-v2/"):
            raise ValueError("Practice audio ownership does not match.")
        now = datetime.now(UTC)
        await self.session.execute(
            insert(PracticeCleanupRow)
            .values(storage_path=path, user_id=owner, attempts=0, next_attempt_at=now)
            .on_conflict_do_update(
                index_elements=[PracticeCleanupRow.storage_path],
                set_={"attempts": 0, "next_attempt_at": now},
            )
        )
        await self.session.commit()


class InMemoryPracticeRepository:
    def __init__(self):
        self.runs: dict[UUID, Run] = {}
        self.cleanup: dict[str, UUID] = {}

    async def get(self, owner, run_id):
        run = self.runs.get(run_id)
        return deepcopy(run) if run and run.user_id == owner else None

    async def current(self, owner):
        runs = [run for run in self.runs.values() if run.user_id == owner]
        return deepcopy(max(runs, key=lambda run: run.created_at)) if runs else None

    async def find_key(self, owner, key):
        return next(
            (
                deepcopy(run)
                for run in self.runs.values()
                if run.user_id == owner and run.idempotency_key == key
            ),
            None,
        )

    async def create(self, run):
        existing = await self.find_key(run.user_id, run.idempotency_key)
        if existing:
            return existing
        self.runs[run.id] = deepcopy(run)
        return run

    async def save(self, run):
        existing = self.runs.get(run.id)
        if existing is None or existing.revision != run.revision:
            raise ValueError("Practice changed in another request. Reload before retrying.")
        run.revision += 1
        self.runs[run.id] = deepcopy(run)
        return run

    async def remove(self, owner, run_id, expected_revision=None):
        run = await self.get(owner, run_id)
        if expected_revision is not None and (run is None or run.revision != expected_revision):
            raise ValueError("Practice changed before completion. Reload and retry.")
        if run:
            self.cleanup.update({answer.audio_path: owner for answer in run.answers})
            del self.runs[run_id]

    async def expire(self, now, owner=None):
        for run in list(self.runs.values()):
            if run.expires_at <= now and (owner is None or run.user_id == owner):
                await self.remove(run.user_id, run.id)

    async def queue_audio_cleanup(self, owner, path):
        if not path.startswith(f"{owner}/practice-v2/"):
            raise ValueError("Practice audio ownership does not match.")
        self.cleanup[path] = owner
