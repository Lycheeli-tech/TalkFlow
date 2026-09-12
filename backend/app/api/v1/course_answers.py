from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.api.core_dependencies import get_course_current_user
from app.api.course_dependencies import get_course_answer_service
from app.core.auth import AuthenticatedUser
from app.course.answer_schemas import CourseAnswerView
from app.course.answer_service import CourseAnswerService

router = APIRouter()


@router.get("/{answer_id}", response_model=CourseAnswerView)
async def get_answer(
    answer_id: UUID,
    current_user: AuthenticatedUser = Depends(get_course_current_user),
    service: CourseAnswerService = Depends(get_course_answer_service),
) -> CourseAnswerView:
    try:
        return CourseAnswerView.from_aggregate(
            await service.get(user_id=current_user.id, answer_id=answer_id)
        )
    except LookupError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.post("/{answer_id}/retry", response_model=CourseAnswerView)
async def retry_answer(
    answer_id: UUID,
    current_user: AuthenticatedUser = Depends(get_course_current_user),
    service: CourseAnswerService = Depends(get_course_answer_service),
) -> CourseAnswerView:
    try:
        return CourseAnswerView.from_aggregate(
            await service.retry(user_id=current_user.id, answer_id=answer_id)
        )
    except LookupError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error


@router.get("/{answer_id}/audio")
async def get_answer_audio(
    answer_id: UUID,
    current_user: AuthenticatedUser = Depends(get_course_current_user),
    service: CourseAnswerService = Depends(get_course_answer_service),
) -> Response:
    try:
        audio, content_type = await service.audio_for(user_id=current_user.id, answer_id=answer_id)
    except LookupError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    return Response(audio, media_type=content_type)
