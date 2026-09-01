from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user, get_memory_repository
from app.repositories.memory import MemoryRepository
from app.schemas import AuthenticatedUser, Expression
from app.services.memory import MemoryApplicationService

router = APIRouter()


@router.get("/expressions", response_model=list[Expression])
async def list_expressions(
    current_user: AuthenticatedUser = Depends(get_current_user),
    repository: MemoryRepository = Depends(get_memory_repository),
) -> list[Expression]:
    return await MemoryApplicationService(repository).list_expressions(current_user.id)
