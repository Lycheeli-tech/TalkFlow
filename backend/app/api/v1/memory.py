from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import (
    get_current_user,
    get_memory_repository,
    get_retrieval_opportunity_repository,
)
from app.repositories.memory import MemoryRepository
from app.repositories.retrieval import RetrievalOpportunityRepository
from app.schemas import AuthenticatedUser, Expression, RetrievalOpportunity
from app.services.memory import MemoryApplicationService
from app.services.retrieval import RetrievalService

router = APIRouter()


@router.get("/expressions", response_model=list[Expression])
async def list_expressions(
    current_user: AuthenticatedUser = Depends(get_current_user),
    repository: MemoryRepository = Depends(get_memory_repository),
) -> list[Expression]:
    return await MemoryApplicationService(repository).list_expressions(current_user.id)


@router.get("/retrieval/due", response_model=list[RetrievalOpportunity])
async def list_due_retrieval(
    session_id: UUID,
    question_family: str,
    question_text: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    repository: MemoryRepository = Depends(get_memory_repository),
    opportunities: RetrievalOpportunityRepository = Depends(get_retrieval_opportunity_repository),
) -> RetrievalOpportunity:
    opportunity = await RetrievalService(repository, opportunities).create_due_opportunity(
        user_id=current_user.id,
        session_id=session_id,
        question_family=question_family,
        question_text=question_text,
    )
    if opportunity is None:
        raise HTTPException(status_code=404, detail="No expression is due for retrieval.")
    return opportunity
