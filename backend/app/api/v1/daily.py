from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status

from app.ai.interfaces import AnswerAnalyzer, LLMService, SpeechToTextService, TextToSpeechService
from app.api.dependencies import (
    get_answer_analyzer,
    get_audio_storage,
    get_current_user,
    get_daily_session_repository,
    get_llm_service,
    get_memory_repository,
    get_profile_repository,
    get_retrieval_opportunity_repository,
    get_stt_service,
    get_tts_service,
    get_user_repository,
    get_voice_attempt_repository,
)
from app.core.config import get_settings
from app.curriculum.interview_bootcamp_v1 import LANGUAGE_INVENTORY
from app.repositories.calibration import VoiceAttemptRepository
from app.repositories.daily_sessions import DailySessionRepository
from app.repositories.memory import MemoryRepository
from app.repositories.profiles import ProfileRepository
from app.repositories.retrieval import RetrievalOpportunityRepository
from app.repositories.users import UserRepository
from app.schemas import (
    AuthenticatedUser,
    DailySessionCompletion,
    DailySessionResponse,
    DailyStep,
    Expression,
    RetrievalOpportunityResponse,
    RetrievalResult,
    VoiceAttempt,
)
from app.services.daily_lesson_content import DailyLessonContentService
from app.services.daily_planner import DailyPlanner, DailyPlannerInput
from app.services.daily_voice import VOICE_STEPS, DailyVoiceService
from app.services.memory import MemoryApplicationService
from app.services.retrieval import RetrievalService
from app.storage.audio import AudioStorage

router = APIRouter()


def daily_voice_service(
    sessions: DailySessionRepository = Depends(get_daily_session_repository),
    attempts: VoiceAttemptRepository = Depends(get_voice_attempt_repository),
    stt: SpeechToTextService = Depends(get_stt_service),
    tts: TextToSpeechService = Depends(get_tts_service),
    analyzer: AnswerAnalyzer = Depends(get_answer_analyzer),
    audio: AudioStorage = Depends(get_audio_storage),
    opportunities: RetrievalOpportunityRepository = Depends(get_retrieval_opportunity_repository),
) -> DailyVoiceService:
    return DailyVoiceService(
        sessions=sessions,
        attempts=attempts,
        stt=stt,
        tts=tts,
        analyzer=analyzer,
        audio=audio,
        opportunities=opportunities,
    )


async def _with_retrieval(
    session: DailySessionResponse,
    *,
    user_id: UUID,
    memory: MemoryRepository,
    opportunities: RetrievalOpportunityRepository,
) -> DailySessionResponse:
    question = (
        session.content.follow_up_questions[0]
        if session.content.follow_up_questions
        else session.content.question_prompt
    )
    opportunity = await RetrievalService(memory, opportunities).create_due_opportunity(
        user_id=user_id,
        session_id=session.session_id,
        question_family=session.plan.question_family,
        question_text=question,
    )
    if opportunity is None:
        return session
    safe = RetrievalOpportunityResponse(
        opportunity_id=opportunity.id,
        session_id=opportunity.session_id,
        question_family=opportunity.question_family,
        question_text=opportunity.question_text,
        status=opportunity.status,
    )
    result = None
    if opportunity.status == "CONSUMED":
        expression = await memory.get_expression(opportunity.expression_id, user_id)
        if expression is not None:
            result = RetrievalResult(
                opportunity_id=opportunity.id,
                recorded=False,
                expression_status=expression.status,
                next_review_at=expression.next_review_at,
            )
    return session.model_copy(update={"retrieval_opportunity": safe, "retrieval_result": result})


@router.post("/sessions", response_model=DailySessionResponse)
async def create_daily_session(
    current_user: AuthenticatedUser = Depends(get_current_user),
    profiles: ProfileRepository = Depends(get_profile_repository),
    repository: DailySessionRepository = Depends(get_daily_session_repository),
    llm: LLMService = Depends(get_llm_service),
    users: UserRepository = Depends(get_user_repository),
    memory: MemoryRepository = Depends(get_memory_repository),
    opportunities: RetrievalOpportunityRepository = Depends(get_retrieval_opportunity_repository),
) -> DailySessionResponse:
    profile = await profiles.get_confirmed(current_user.id)
    if profile is None:
        raise HTTPException(status_code=409, detail="A confirmed profile is required first.")
    user = await users.get_or_create(current_user.id)
    if user.program_completed_at is not None:
        raise HTTPException(status_code=409, detail="The 30-day Bootcamp is complete.")
    plan = DailyPlanner().plan(
        DailyPlannerInput(
            profile=profile,
            assessment=None,
            current_day=user.current_day,
            duration_minutes=user.default_session_length,
        )
    )
    content = await DailyLessonContentService(llm=llm).generate(plan=plan, profile=profile)
    session = await repository.get_or_create(user_id=current_user.id, plan=plan, content=content)
    if not hasattr(memory, "list_expressions") or not hasattr(opportunities, "get_for_session"):
        return session
    return await _with_retrieval(
        session, user_id=current_user.id, memory=memory, opportunities=opportunities
    )


@router.post("/sessions/{session_id}/complete", response_model=DailySessionCompletion)
async def complete_daily_session(
    session_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    repository: DailySessionRepository = Depends(get_daily_session_repository),
    memory: MemoryRepository = Depends(get_memory_repository),
) -> DailySessionCompletion:
    try:
        session = await repository.get(user_id=current_user.id, session_id=session_id)
        if session is None:
            raise LookupError("Daily session not found.")
        completion = await repository.complete(user_id=current_user.id, session_id=session_id)
        if session.plan.day == 1:
            existing = {
                item.text.casefold() for item in await memory.list_expressions(current_user.id)
            }
            learned_at = datetime.now(UTC)
            service = MemoryApplicationService(memory)
            for target_id in session.plan.new_language_target_ids:
                target = next((item for item in LANGUAGE_INVENTORY if item.id == target_id), None)
                if target is not None and target.content.casefold() not in existing:
                    await service.create_expression(
                        Expression(
                            id=uuid4(),
                            user_id=current_user.id,
                            text=target.content,
                            meaning="Useful spoken interview expression",
                            source_type="CURRICULUM",
                            status="LEARNING",
                            next_review_at=learned_at + timedelta(days=1),
                            created_at=learned_at,
                            updated_at=learned_at,
                        )
                    )
        return completion
    except LookupError as error:
        raise HTTPException(status_code=404, detail="Daily session not found.") from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.get("/sessions/{session_id}/attempts", response_model=list[VoiceAttempt])
async def list_daily_attempts(
    session_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    service: DailyVoiceService = Depends(daily_voice_service),
) -> list[VoiceAttempt]:
    try:
        return await service.list_attempts(user_id=current_user.id, session_id=session_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/sessions/{session_id}/steps/{step}/tts")
async def daily_step_tts(
    session_id: UUID,
    step: DailyStep,
    current_user: AuthenticatedUser = Depends(get_current_user),
    service: DailyVoiceService = Depends(daily_voice_service),
) -> Response:
    try:
        audio = await service.synthesize(user_id=current_user.id, session_id=session_id, step=step)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return Response(audio, media_type="audio/mpeg")


@router.post("/sessions/{session_id}/attempts", response_model=VoiceAttempt)
async def submit_daily_attempt(
    session_id: UUID,
    step: Annotated[DailyStep, Form()],
    response_duration_ms: Annotated[int | None, Form()] = None,
    recording: UploadFile = File(...),
    current_user: AuthenticatedUser = Depends(get_current_user),
    service: DailyVoiceService = Depends(daily_voice_service),
) -> VoiceAttempt:
    content = await recording.read()
    if not content:
        raise HTTPException(status_code=422, detail="Recording cannot be empty.")
    if len(content) > get_settings().max_audio_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Recording is too large.",
        )
    if not (recording.content_type or "").startswith("audio/"):
        raise HTTPException(status_code=415, detail="An audio recording is required.")
    try:
        return await service.submit(
            user_id=current_user.id,
            session_id=session_id,
            step=step,
            audio=content,
            content_type=recording.content_type or "application/octet-stream",
            duration_ms=response_duration_ms,
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.post("/attempts/{attempt_id}/retry", response_model=VoiceAttempt)
async def retry_daily_attempt(
    attempt_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    service: DailyVoiceService = Depends(daily_voice_service),
) -> VoiceAttempt:
    try:
        return await service.retry(user_id=current_user.id, attempt_id=attempt_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.post("/sessions/{session_id}/advance", response_model=DailySessionResponse)
async def advance_daily_session(
    session_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    repository: DailySessionRepository = Depends(get_daily_session_repository),
    attempts: VoiceAttemptRepository = Depends(get_voice_attempt_repository),
) -> DailySessionResponse:
    try:
        session = await repository.get(user_id=current_user.id, session_id=session_id)
        if session is None:
            raise LookupError("Daily session not found.")
        step = session.plan.steps[session.current_step]
        if step in VOICE_STEPS:
            saved = await attempts.list_attempts(session_id, current_user.id)
            if not any(item.question_type == step and item.status == "ANALYZED" for item in saved):
                raise ValueError("Complete the current voice step before continuing.")
        return await repository.advance(user_id=current_user.id, session_id=session_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail="Daily session not found.") from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
