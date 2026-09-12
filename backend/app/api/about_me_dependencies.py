from collections.abc import AsyncIterator
from functools import lru_cache

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.about_me.memory_ai import (
    BailianMemoryDecisionProposer,
    IgnoreMemoryDecisionProposer,
    MemoryDecisionProposer,
)
from app.about_me.repository import AboutMeRepository, SQLAboutMeRepository
from app.about_me.service import AboutMeService
from app.core.config import get_settings
from app.db.session import get_database_session
from app.services.documents import PdfResumeParser
from app.storage.documents import DocumentStorage, build_document_storage


async def get_about_me_repository(
    session: AsyncSession = Depends(get_database_session),
) -> AsyncIterator[AboutMeRepository]:
    yield SQLAboutMeRepository(session)


@lru_cache
def get_about_me_storage() -> DocumentStorage:
    return build_document_storage()


@lru_cache
def get_memory_decision_proposer() -> MemoryDecisionProposer:
    settings = get_settings()
    provider = settings.memory_provider or settings.llm_provider
    if provider == "bailian":
        if not settings.bailian_api_key:
            raise RuntimeError("BAILIAN_API_KEY is required for AI Memory.")
        return BailianMemoryDecisionProposer(
            api_key=settings.bailian_api_key,
            base_url=settings.bailian_compatible_base_url,
            model=settings.bailian_text_model,
        )
    return IgnoreMemoryDecisionProposer()


def get_about_me_service(
    repository: AboutMeRepository = Depends(get_about_me_repository),
    storage: DocumentStorage = Depends(get_about_me_storage),
    memory: MemoryDecisionProposer = Depends(get_memory_decision_proposer),
) -> AboutMeService:
    return AboutMeService(
        repository=repository,
        storage=storage,
        parser=PdfResumeParser(get_settings().max_resume_bytes),
        memory=memory,
    )
