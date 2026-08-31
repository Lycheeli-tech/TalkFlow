from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, SmallInteger, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserRow(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "public"}

    id: Mapped[UUID] = mapped_column(primary_key=True)
    interface_language: Mapped[str] = mapped_column(String(8), default="en")
    support_language: Mapped[str] = mapped_column(String(8), default="en")
    default_session_length: Mapped[int] = mapped_column(SmallInteger, default=20)
    coaching_style: Mapped[str] = mapped_column(String(16), default="supportive")
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
