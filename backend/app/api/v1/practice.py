from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_current_user, get_mock_interview_service
from app.schemas import (
    AuthenticatedUser,
    MockInterviewPrompt,
    MockInterviewRequest,
    MockInterviewResult,
)
from app.services.mock_interview import MockInterviewService

router = APIRouter()


@router.get("/mock-interview/prompt", response_model=MockInterviewPrompt)
async def get_mock_interview_prompt(
    question_id: str | None = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
    service: MockInterviewService = Depends(get_mock_interview_service),
) -> MockInterviewPrompt:
    del current_user
    return service.prompt(question_id)


@router.post("/mock-interview/evaluate", response_model=MockInterviewResult)
async def evaluate_mock_interview(
    request: MockInterviewRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    service: MockInterviewService = Depends(get_mock_interview_service),
) -> MockInterviewResult:
    del current_user
    try:
        return await service.evaluate(
            question_id=request.question_id, transcript=request.transcript
        )
    except Exception as error:
        raise HTTPException(status_code=502, detail="Interview analysis is unavailable.") from error
