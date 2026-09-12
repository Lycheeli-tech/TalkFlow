from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status

from app.api.core_dependencies import get_course_current_user
from app.api.course_dependencies import get_course_answer_service
from app.core.auth import AuthenticatedUser
from app.core.config import get_settings
from app.course.answer_schemas import CourseAnswerView, CourseHistoryResponse
from app.course.answer_service import CourseAnswerService
from app.course.catalog_v1 import COURSE_CATALOG_V1, COURSES_BY_ID
from app.course.schemas import CourseCatalogItem, CourseCatalogResponse

router = APIRouter()


@router.get("", response_model=CourseCatalogResponse)
def list_courses() -> CourseCatalogResponse:
    return CourseCatalogResponse(
        courses=tuple(CourseCatalogItem.from_definition(course) for course in COURSE_CATALOG_V1)
    )


@router.get("/{course_id}", response_model=CourseCatalogItem)
def get_course(course_id: str) -> CourseCatalogItem:
    course = COURSES_BY_ID.get(course_id)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found.")
    return CourseCatalogItem.from_definition(course)


@router.get("/{course_id}/questions/{question_id}/history", response_model=CourseHistoryResponse)
async def get_question_history(
    course_id: str,
    question_id: str,
    current_user: AuthenticatedUser = Depends(get_course_current_user),
    service: CourseAnswerService = Depends(get_course_answer_service),
) -> CourseHistoryResponse:
    try:
        answers = await service.history(
            user_id=current_user.id, course_id=course_id, question_id=question_id
        )
    except LookupError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except PermissionError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    views = tuple(CourseAnswerView.from_aggregate(answer) for answer in answers)
    return CourseHistoryResponse(
        course_id=course_id, question_id=question_id, count=len(views), answers=views
    )


@router.post(
    "/{course_id}/questions/{question_id}/answers",
    response_model=CourseAnswerView,
    status_code=status.HTTP_201_CREATED,
)
async def submit_english_answer(
    course_id: str,
    question_id: str,
    idempotency_key: Annotated[str, Form(min_length=8, max_length=128)],
    recording: UploadFile = File(...),
    response_duration_ms: Annotated[int | None, Form(ge=0)] = None,
    current_user: AuthenticatedUser = Depends(get_course_current_user),
    service: CourseAnswerService = Depends(get_course_answer_service),
) -> CourseAnswerView:
    content = await recording.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Recording cannot be empty."
        )
    if len(content) > get_settings().max_audio_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Recording is too large."
        )
    content_type = recording.content_type or ""
    if not content_type.startswith("audio/"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="An audio recording is required.",
        )
    try:
        aggregate = await service.submit_english(
            user_id=current_user.id,
            course_id=course_id,
            question_id=question_id,
            idempotency_key=idempotency_key,
            audio=content,
            content_type=content_type,
            duration_ms=response_duration_ms,
        )
    except LookupError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except PermissionError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    return CourseAnswerView.from_aggregate(aggregate)


@router.get("/{course_id}/questions/{question_id}/tts")
async def question_tts(
    course_id: str,
    question_id: str,
    current_user: AuthenticatedUser = Depends(get_course_current_user),
    service: CourseAnswerService = Depends(get_course_answer_service),
) -> Response:
    del current_user
    try:
        audio = await service.synthesize_question(course_id=course_id, question_id=question_id)
    except LookupError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except PermissionError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    return Response(audio, media_type="audio/mpeg")
