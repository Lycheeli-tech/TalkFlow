from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import (
    get_current_user,
    get_memory_repository,
    get_retrieval_opportunity_repository,
    get_verification_service,
)
from app.repositories.memory import MemoryRepository
from app.repositories.retrieval import RetrievalOpportunityRepository
from app.schemas import (
    AuthenticatedUser,
    Expression,
    ResolveRetrievalRequest,
    RetrievalOpportunityResponse,
    RetrievalResult,
)
from app.services.memory import MemoryApplicationService
from app.services.retrieval import RetrievalService
from app.services.verification import VerificationService

router = APIRouter()


@router.get("/expressions", response_model=list[Expression])
async def list_expressions(
    current_user: AuthenticatedUser = Depends(get_current_user),
    repository: MemoryRepository = Depends(get_memory_repository),
) -> list[Expression]:
    return await MemoryApplicationService(repository).list_expressions(current_user.id)


@router.get("/retrieval/due", response_model=RetrievalOpportunityResponse)
async def list_due_retrieval(
    session_id: UUID,
    question_family: str,
    question_text: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    repository: MemoryRepository = Depends(get_memory_repository),
    opportunities: RetrievalOpportunityRepository = Depends(get_retrieval_opportunity_repository),
) -> RetrievalOpportunityResponse:
    opportunity = await RetrievalService(repository, opportunities).create_due_opportunity(
        user_id=current_user.id,
        session_id=session_id,
        question_family=question_family,
        question_text=question_text,
    )
    if opportunity is None:
        raise HTTPException(status_code=404, detail="No expression is due for retrieval.")
    return RetrievalOpportunityResponse(
        opportunity_id=opportunity.id,
        session_id=opportunity.session_id,
        question_family=opportunity.question_family,
        question_text=opportunity.question_text,
        status=opportunity.status,
    )


@router.post("/retrieval/{opportunity_id}/resolve", response_model=RetrievalResult)
async def resolve_retrieval(
    opportunity_id: UUID,
    request: ResolveRetrievalRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    verifier: VerificationService = Depends(get_verification_service),
) -> RetrievalResult:
    try:
        return await verifier.verify_and_record(
            user_id=current_user.id,
            opportunity_id=opportunity_id,
            attempt_id=request.attempt_id,
        )
    except (LookupError, PermissionError, ValueError) as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
