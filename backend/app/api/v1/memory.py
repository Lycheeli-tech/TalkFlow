from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user, get_memory_repository
from app.repositories.memory import MemoryRepository
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
    current_user: AuthenticatedUser = Depends(get_current_user),
    repository: MemoryRepository = Depends(get_memory_repository),
) -> list[RetrievalOpportunity]:
    return await RetrievalService(repository).due_opportunities(user_id=current_user.id)
