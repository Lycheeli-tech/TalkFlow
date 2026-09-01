from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status

from app.ai.interfaces import (
    AnswerAnalyzer,
    CalibrationQuestionGenerator,
    SpeechToTextService,
    TextToSpeechService,
)
from app.api.dependencies import (
    get_answer_analyzer,
    get_audio_storage,
    get_calibration_repository,
    get_current_user,
    get_profile_repository,
    get_question_generator,
    get_stt_service,
    get_tts_service,
)
from app.core.config import get_settings
from app.repositories.calibration import CalibrationRepository
from app.repositories.profiles import ProfileRepository
from app.schemas import AuthenticatedUser, CalibrationResult, CalibrationSession, VoiceAttempt
from app.services.calibration import CalibrationService
from app.storage.audio import AudioStorage

router = APIRouter()


def calibration_service(
    repository: CalibrationRepository = Depends(get_calibration_repository),
    profiles: ProfileRepository = Depends(get_profile_repository),
    questions: CalibrationQuestionGenerator = Depends(get_question_generator),
    stt: SpeechToTextService = Depends(get_stt_service),
    tts: TextToSpeechService = Depends(get_tts_service),
    analyzer: AnswerAnalyzer = Depends(get_answer_analyzer),
    audio: AudioStorage = Depends(get_audio_storage),
) -> CalibrationService:
    return CalibrationService(
        repository=repository,
        profiles=profiles,
        questions=questions,
        stt=stt,
        tts=tts,
        analyzer=analyzer,
        audio=audio,
    )


@router.post("/sessions", response_model=CalibrationSession, status_code=status.HTTP_201_CREATED)
async def start_calibration(
    current_user: AuthenticatedUser = Depends(get_current_user),
    service: CalibrationService = Depends(calibration_service),
) -> CalibrationSession:
    try:
        return await service.start(current_user.id)
    except PermissionError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error


@router.get("/sessions/{session_id}/questions/{category}/tts")
async def question_tts(
    session_id: UUID,
    category: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    service: CalibrationService = Depends(calibration_service),
) -> Response:
    try:
        audio = await service.synthesize(
            user_id=current_user.id, session_id=session_id, category=category
        )
    except LookupError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    return Response(audio, media_type="audio/mpeg")


@router.post("/sessions/{session_id}/attempts", response_model=VoiceAttempt)
async def submit_attempt(
    session_id: UUID,
    category: Annotated[str, Form()],
    response_duration_ms: Annotated[int | None, Form()] = None,
    recording: UploadFile = File(...),
    current_user: AuthenticatedUser = Depends(get_current_user),
    service: CalibrationService = Depends(calibration_service),
) -> VoiceAttempt:
    content = await recording.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Recording cannot be empty."
        )
    if len(content) > get_settings().max_audio_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Recording is too large."
        )
    if not (recording.content_type or "").startswith("audio/"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="An audio recording is required.",
        )
    try:
        return await service.submit(
            user_id=current_user.id,
            session_id=session_id,
            category=category,
            audio=content,
            content_type=recording.content_type or "application/octet-stream",
            duration_ms=response_duration_ms,
        )
    except LookupError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.post("/attempts/{attempt_id}/retry", response_model=VoiceAttempt)
async def retry_attempt(
    attempt_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    service: CalibrationService = Depends(calibration_service),
) -> VoiceAttempt:
    try:
        return await service.retry(user_id=current_user.id, attempt_id=attempt_id)
    except LookupError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.get("/sessions/{session_id}", response_model=CalibrationResult)
async def get_calibration(
    session_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    service: CalibrationService = Depends(calibration_service),
) -> CalibrationResult:
    try:
        session, attempts, assessment = await service.result(
            user_id=current_user.id, session_id=session_id
        )
    except LookupError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    return CalibrationResult(session=session, attempts=attempts, assessment=assessment)
