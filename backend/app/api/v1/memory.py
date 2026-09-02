from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_current_user,
    get_memory_repository,
    get_retrieval_opportunity_repository,
    get_verification_service,
)
from app.db.models import AttemptRow
from app.db.session import get_database_session
from app.repositories.memory import MemoryRepository
from app.repositories.retrieval import RetrievalOpportunityRepository
from app.schemas import (
    AuthenticatedUser,
    Expression,
    MyEnglishResponse,
    QuickReviewItem,
    QuickReviewSubmit,
    ResolveRetrievalRequest,
    RetrievalOpportunityResponse,
    RetrievalResult,
    TrustedTransferAnalysis,
)
from app.services.memory import MemoryApplicationService
from app.services.quick_review import QuickReviewService
from app.services.retrieval import RetrievalService
from app.services.verification import VerificationService

router = APIRouter()


@router.get("/expressions", response_model=list[Expression])
async def list_expressions(
    current_user: AuthenticatedUser = Depends(get_current_user),
    repository: MemoryRepository = Depends(get_memory_repository),
) -> list[Expression]:
    return await MemoryApplicationService(repository).list_expressions(current_user.id)


@router.get("/my-english", response_model=MyEnglishResponse)
async def get_my_english(
    current_user: AuthenticatedUser = Depends(get_current_user),
    repository: MemoryRepository = Depends(get_memory_repository),
) -> MyEnglishResponse:
    return await MemoryApplicationService(repository).my_english(current_user.id)


@router.get("/quick-review", response_model=list[QuickReviewItem])
async def list_quick_review(
    limit: int = 10,
    current_user: AuthenticatedUser = Depends(get_current_user),
    repository: MemoryRepository = Depends(get_memory_repository),
) -> list[QuickReviewItem]:
    try:
        return await QuickReviewService(repository).list_due(current_user.id, limit=limit)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.post("/quick-review/start", response_model=RetrievalOpportunityResponse)
async def start_quick_review(
    session_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    repository: MemoryRepository = Depends(get_memory_repository),
    opportunities: RetrievalOpportunityRepository = Depends(get_retrieval_opportunity_repository),
) -> RetrievalOpportunityResponse:
    try:
        opportunity = await RetrievalService(repository, opportunities).create_due_opportunity(
            user_id=current_user.id,
            session_id=session_id,
            question_family="QUICK_REVIEW",
            question_text=(
                "Tell me about a recent experience where you applied something you learned."
            ),
        )
    except (LookupError, PermissionError, ValueError) as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    if opportunity is None:
        raise HTTPException(status_code=404, detail="No expression is due for review.")
    return RetrievalOpportunityResponse(
        opportunity_id=opportunity.id,
        session_id=opportunity.session_id,
        question_family=opportunity.question_family,
        question_text=opportunity.question_text,
        status=opportunity.status,
    )


@router.post("/quick-review/{opportunity_id}/submit", response_model=RetrievalResult)
async def submit_quick_review(
    opportunity_id: UUID,
    request: QuickReviewSubmit,
    current_user: AuthenticatedUser = Depends(get_current_user),
    repository: MemoryRepository = Depends(get_memory_repository),
    opportunities: RetrievalOpportunityRepository = Depends(get_retrieval_opportunity_repository),
    session: AsyncSession = Depends(get_database_session),
    verifier: VerificationService = Depends(get_verification_service),
) -> RetrievalResult:
    opportunity = await opportunities.get(opportunity_id, current_user.id)
    if opportunity is None:
        raise HTTPException(status_code=404, detail="Review opportunity was not found.")
    if opportunity.status != "CREATED":
        raise HTTPException(status_code=409, detail="Review opportunity has already been resolved.")
    expression = await repository.get_expression(opportunity.expression_id, current_user.id)
    if expression is None:
        raise HTTPException(status_code=404, detail="Review target was not found.")
    attempt_id = uuid4()
    normalized = request.transcript.casefold()
    analysis = TrustedTransferAnalysis(
        target_used=expression.text.casefold() in normalized,
        usage_correct=expression.text.casefold() in normalized,
        direct_hint_used=False,
        verifier_version="quick_review_verifier_v1",
    )
    session.add(
        AttemptRow(
            id=attempt_id,
            session_id=opportunity.session_id,
            user_id=current_user.id,
            question=opportunity.question_text,
            question_type="QUICK_REVIEW",
            audio_path=f"quick-review://{attempt_id}",
            audio_content_type="text/plain",
            transcript=request.transcript,
            analysis=analysis.model_dump(),
            status="ANALYZED",
            analyzer_version=analysis.verifier_version,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
    )
    await session.commit()
    try:
        return await verifier.verify_and_record(
            user_id=current_user.id, opportunity_id=opportunity_id, attempt_id=attempt_id
        )
    except (LookupError, PermissionError, ValueError) as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


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
