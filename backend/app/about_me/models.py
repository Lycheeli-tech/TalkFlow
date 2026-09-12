from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKeyConstraint, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AboutMeProfileRow(Base):
    __tablename__ = "about_me_profiles"
    __table_args__ = {"schema": "public"}

    user_id: Mapped[UUID] = mapped_column(primary_key=True)
    supplemental_facts: Mapped[list[str]] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class TargetRoleRow(Base):
    __tablename__ = "target_roles"
    __table_args__ = (
        UniqueConstraint("id", "user_id", name="uq_target_role_owner"),
        UniqueConstraint("user_id", "role_name", name="uq_target_role_name"),
        {"schema": "public"},
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    user_id: Mapped[UUID] = mapped_column()
    role_name: Mapped[str] = mapped_column(String(160))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class MemoryItemRow(Base):
    __tablename__ = "memory_items"
    __table_args__ = (
        UniqueConstraint("id", "user_id", name="uq_memory_item_owner"),
        {"schema": "public"},
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    user_id: Mapped[UUID] = mapped_column()
    content: Mapped[str] = mapped_column(Text)
    normalized_content: Mapped[str] = mapped_column(Text)
    extractor_prompt_version: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class MemorySourceRow(Base):
    __tablename__ = "memory_sources"
    __table_args__ = (
        ForeignKeyConstraint(
            ["memory_id", "user_id"],
            ["public.memory_items.id", "public.memory_items.user_id"],
            name="memory_sources_item_owner_fk",
            ondelete="CASCADE",
        ),
        {"schema": "public"},
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    memory_id: Mapped[UUID] = mapped_column()
    user_id: Mapped[UUID] = mapped_column()
    source_type: Mapped[str] = mapped_column(String(32))
    source_id: Mapped[UUID] = mapped_column()
    source_excerpt: Mapped[str] = mapped_column(Text)
    source_field_path: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
