from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.api.core_dependencies import get_course_current_user
from app.api.course_dependencies import get_course_answer_service, get_course_support_service
from app.core.auth import AuthenticatedUser
from app.course.answer_schemas import CourseAnswerView
from app.course.answer_service import CourseAnswerService
from app.course.support_service import CourseSupportService

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


@router.post("/{answer_id}/feedback/retry", response_model=CourseAnswerView)
async def retry_feedback(
    answer_id: UUID,
    current_user: AuthenticatedUser = Depends(get_course_current_user),
    service: CourseSupportService = Depends(get_course_support_service),
) -> CourseAnswerView:
    try:
        return CourseAnswerView.from_aggregate(
            await service.generate_for_answer(user_id=current_user.id, answer_id=answer_id)
        )
    except LookupError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error


@router.post("/{answer_id}/confirm", response_model=CourseAnswerView)
async def confirm_chinese_draft(
    answer_id: UUID,
    current_user: AuthenticatedUser = Depends(get_course_current_user),
    service: CourseAnswerService = Depends(get_course_answer_service),
) -> CourseAnswerView:
    try:
        return CourseAnswerView.from_aggregate(
            await service.confirm(user_id=current_user.id, answer_id=answer_id)
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.delete("/{answer_id}/draft", status_code=204)
async def discard_chinese_draft(
    answer_id: UUID,
    current_user: AuthenticatedUser = Depends(get_course_current_user),
    service: CourseAnswerService = Depends(get_course_answer_service),
) -> Response:
    try:
        await service.discard_draft(user_id=current_user.id, answer_id=answer_id)
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return Response(status_code=204)


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


@router.delete("/{answer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_answer(
    answer_id: UUID,
    current_user: AuthenticatedUser = Depends(get_course_current_user),
    service: CourseAnswerService = Depends(get_course_answer_service),
) -> Response:
    try:
        await service.delete(user_id=current_user.id, answer_id=answer_id)
    except LookupError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)
