from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.ai.interfaces import AnswerAnalyzer, SpeechToTextService, TextToSpeechService
from app.repositories.calibration import VoiceAttemptRepository
from app.repositories.daily_sessions import DailySessionRepository
from app.schemas import DailySessionResponse, DailyStep, VoiceAttempt
from app.storage.audio import AudioStorage

VOICE_STEPS: frozenset[DailyStep] = frozenset(
    {"RECALL", "IMITATE", "RETRIEVE", "TRANSFER", "INTERVIEW"}
)


def prompt_for_step(session: DailySessionResponse, step: DailyStep) -> str:
    content = session.content
    if step == "IMITATE" and content.imitation_variants:
        return content.imitation_variants[0]
    if step == "TRANSFER" and content.transfer_prompts:
        return content.transfer_prompts[0]
    if step == "INTERVIEW" and content.follow_up_questions:
        return content.follow_up_questions[0]
    return content.question_prompt


class DailyVoiceService:
    def __init__(
        self,
        *,
        sessions: DailySessionRepository,
        attempts: VoiceAttemptRepository,
        stt: SpeechToTextService,
        tts: TextToSpeechService,
        analyzer: AnswerAnalyzer,
        audio: AudioStorage,
    ) -> None:
        self._sessions = sessions
        self._attempts = attempts
        self._stt = stt
        self._tts = tts
        self._analyzer = analyzer
        self._audio = audio

    async def synthesize(self, *, user_id: UUID, session_id: UUID, step: DailyStep) -> bytes:
        session = await self._require_current_voice_step(user_id, session_id, step)
        return await self._tts.synthesize(text=prompt_for_step(session, step), voice="default")

    async def submit(
        self,
        *,
        user_id: UUID,
        session_id: UUID,
        step: DailyStep,
        audio: bytes,
        content_type: str,
        duration_ms: int | None,
    ) -> VoiceAttempt:
        session = await self._require_current_voice_step(user_id, session_id, step)
        existing = next(
            (
                item
                for item in await self._attempts.list_attempts(session_id, user_id)
                if item.question_type == step
            ),
            None,
        )
        if existing:
            return existing
        attempt_id = uuid4()
        audio_path = await self._audio.store(
            user_id=user_id,
            session_id=session_id,
            attempt_id=attempt_id,
            content=audio,
            content_type=content_type,
        )
        now = datetime.now(UTC)
        attempt = await self._attempts.save_attempt(
            VoiceAttempt(
                id=attempt_id,
                session_id=session_id,
                user_id=user_id,
                question=prompt_for_step(session, step),
                question_type=step,
                audio_path=audio_path,
                audio_content_type=content_type,
                response_duration_ms=duration_ms,
                created_at=now,
                updated_at=now,
            )
        )
        return await self._process(attempt, audio)

    async def retry(self, *, user_id: UUID, attempt_id: UUID) -> VoiceAttempt:
        attempt = await self._attempts.get_attempt(attempt_id, user_id)
        if attempt is None or attempt.question_type not in VOICE_STEPS:
            raise LookupError("Daily voice attempt was not found for this user.")
        session = await self._sessions.get(user_id=user_id, session_id=attempt.session_id)
        if session is None:
            raise LookupError("Daily session was not found for this user.")
        if session.plan.steps[session.current_step] != attempt.question_type:
            raise ValueError("Only the current Daily voice attempt can be retried.")
        audio = await self._audio.load(path=attempt.audio_path)
        return await self._process(attempt, audio)

    async def list_attempts(self, *, user_id: UUID, session_id: UUID) -> list[VoiceAttempt]:
        if await self._sessions.get(user_id=user_id, session_id=session_id) is None:
            raise LookupError("Daily session was not found for this user.")
        return await self._attempts.list_attempts(session_id, user_id)

    async def _require_current_voice_step(
        self, user_id: UUID, session_id: UUID, step: DailyStep
    ) -> DailySessionResponse:
        session = await self._sessions.get(user_id=user_id, session_id=session_id)
        if session is None:
            raise LookupError("Daily session was not found for this user.")
        current = session.plan.steps[session.current_step]
        if step != current or step not in VOICE_STEPS:
            raise ValueError("Recording is only allowed for the current voice step.")
        return session

    async def _process(self, attempt: VoiceAttempt, audio: bytes) -> VoiceAttempt:
        transcript = attempt.transcript
        if transcript is None:
            try:
                transcript = await self._stt.transcribe(
                    audio=audio, content_type=attempt.audio_content_type
                )
            except Exception as error:
                return await self._attempts.update_attempt(
                    attempt.model_copy(
                        update={
                            "status": "STT_FAILED",
                            "provider_error": str(error),
                            "stt_provider": self._stt.provider_name,
                            "updated_at": datetime.now(UTC),
                        }
                    )
                )
            attempt = await self._attempts.update_attempt(
                attempt.model_copy(
                    update={
                        "transcript": transcript,
                        "status": "TRANSCRIBED",
                        "provider_error": None,
                        "stt_provider": self._stt.provider_name,
                        "updated_at": datetime.now(UTC),
                    }
                )
            )
        try:
            analysis = await self._analyzer.analyze(
                question=attempt.question, transcript=transcript
            )
        except Exception as error:
            return await self._attempts.update_attempt(
                attempt.model_copy(
                    update={
                        "status": "ANALYSIS_FAILED",
                        "provider_error": str(error),
                        "analyzer_version": self._analyzer.version,
                        "updated_at": datetime.now(UTC),
                    }
                )
            )
        return await self._attempts.update_attempt(
            attempt.model_copy(
                update={
                    "analysis": analysis.model_dump(),
                    "status": "ANALYZED",
                    "provider_error": None,
                    "analyzer_version": self._analyzer.version,
                    "updated_at": datetime.now(UTC),
                }
            )
        )
