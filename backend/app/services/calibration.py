from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.ai.interfaces import (
    AnswerAnalyzer,
    CalibrationQuestionGenerator,
    SpeechToTextService,
    TextToSpeechService,
)
from app.repositories.calibration import CalibrationRepository
from app.repositories.profiles import ProfileRepository
from app.schemas import (
    AttemptAnalysis,
    CalibrationQuestion,
    CalibrationSession,
    LearnerAssessment,
    VoiceAttempt,
)
from app.storage.audio import AudioStorage

CATEGORIES = ("EXPERIENCE", "MOTIVATION", "PROJECT")
LEVELS = ("NEEDS_WORK", "DEVELOPING", "FUNCTIONAL", "STRONG")


class CalibrationService:
    def __init__(
        self,
        *,
        repository: CalibrationRepository,
        profiles: ProfileRepository,
        questions: CalibrationQuestionGenerator,
        stt: SpeechToTextService,
        tts: TextToSpeechService,
        analyzer: AnswerAnalyzer,
        audio: AudioStorage,
    ) -> None:
        self._repository = repository
        self._profiles = profiles
        self._questions = questions
        self._stt = stt
        self._tts = tts
        self._analyzer = analyzer
        self._audio = audio

    async def start(self, user_id: UUID) -> CalibrationSession:
        profile = await self._profiles.get_confirmed(user_id)
        if profile is None:
            raise PermissionError("A confirmed profile is required before voice calibration.")
        questions = await self._questions.generate(profile=profile)
        self._validate_questions(questions)
        now = datetime.now(UTC)
        return await self._repository.create_session(
            CalibrationSession(id=uuid4(), user_id=user_id, questions=questions, started_at=now)
        )

    async def synthesize(
        self, *, user_id: UUID, session_id: UUID, category: str, voice: str = "default"
    ) -> bytes:
        question = await self._question(user_id, session_id, category)
        return await self._tts.synthesize(text=question.text, voice=voice)

    async def submit(
        self,
        *,
        user_id: UUID,
        session_id: UUID,
        category: str,
        audio: bytes,
        content_type: str,
        duration_ms: int | None,
    ) -> VoiceAttempt:
        question = await self._question(user_id, session_id, category)
        existing = next(
            (
                item
                for item in await self._repository.list_attempts(session_id, user_id)
                if item.question_type == category
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
        attempt = await self._repository.save_attempt(
            VoiceAttempt(
                id=attempt_id,
                session_id=session_id,
                user_id=user_id,
                question=question.text,
                question_type=category,
                audio_path=audio_path,
                audio_content_type=content_type,
                response_duration_ms=duration_ms,
                created_at=now,
                updated_at=now,
            )
        )
        return await self._process(attempt, audio)

    async def retry(self, *, user_id: UUID, attempt_id: UUID) -> VoiceAttempt:
        attempt = await self._repository.get_attempt(attempt_id, user_id)
        if attempt is None:
            raise LookupError("Attempt was not found for this user.")
        if attempt.status == "ANALYZED":
            return attempt
        audio = await self._audio.load(path=attempt.audio_path)
        return await self._process(attempt, audio)

    async def result(
        self, *, user_id: UUID, session_id: UUID
    ) -> tuple[CalibrationSession, list[VoiceAttempt], LearnerAssessment | None]:
        session = await self._repository.get_session(session_id, user_id)
        if session is None:
            raise LookupError("Calibration session was not found for this user.")
        return (
            session,
            await self._repository.list_attempts(session_id, user_id),
            await self._repository.get_assessment(session_id, user_id),
        )

    async def _process(self, attempt: VoiceAttempt, audio: bytes) -> VoiceAttempt:
        transcript = attempt.transcript
        if transcript is None:
            try:
                transcript = await self._stt.transcribe(
                    audio=audio, content_type=attempt.audio_content_type
                )
            except Exception as error:
                return await self._repository.update_attempt(
                    attempt.model_copy(
                        update={
                            "status": "STT_FAILED",
                            "provider_error": str(error),
                            "stt_provider": self._stt.provider_name,
                            "updated_at": datetime.now(UTC),
                        }
                    )
                )
            attempt = await self._repository.update_attempt(
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
            return await self._repository.update_attempt(
                attempt.model_copy(
                    update={
                        "status": "ANALYSIS_FAILED",
                        "provider_error": str(error),
                        "analyzer_version": self._analyzer.version,
                        "updated_at": datetime.now(UTC),
                    }
                )
            )
        attempt = await self._repository.update_attempt(
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
        await self._aggregate_if_complete(attempt.session_id, attempt.user_id)
        return attempt

    async def _aggregate_if_complete(self, session_id: UUID, user_id: UUID) -> None:
        attempts = await self._repository.list_attempts(session_id, user_id)
        if len(attempts) != 3 or any(item.status != "ANALYZED" for item in attempts):
            return
        if await self._repository.get_assessment(session_id, user_id):
            return
        analyses = [AttemptAnalysis.model_validate(item.analysis) for item in attempts]

        def median(field: str) -> str:
            values = sorted(LEVELS.index(getattr(item, field)) for item in analyses)
            return LEVELS[values[1]]

        focuses = [value for item in analyses for value in item.focus_areas]
        assessment = LearnerAssessment(
            id=uuid4(),
            session_id=session_id,
            user_id=user_id,
            fluency=median("fluency"),
            naturalness=median("naturalness"),
            grammar=median("grammar"),
            retrieval=median("retrieval"),
            structure=median("structure"),
            strengths=list(dict.fromkeys(value for item in analyses for value in item.strengths)),
            primary_focus=focuses[0]
            if focuses
            else "Build clearer, more specific interview answers.",
            secondary_focus=focuses[1] if len(focuses) > 1 else None,
            observed_patterns=list(
                dict.fromkeys(value for item in analyses for value in item.observed_patterns)
            ),
            assessment_version="learner_assessment_v1",
            created_at=datetime.now(UTC),
        )
        await self._repository.save_assessment(assessment)
        await self._repository.complete_session(session_id, user_id)

    async def _question(
        self, user_id: UUID, session_id: UUID, category: str
    ) -> CalibrationQuestion:
        session = await self._repository.get_session(session_id, user_id)
        if session is None:
            raise LookupError("Calibration session was not found for this user.")
        return next((item for item in session.questions if item.category == category), None) or (
            _ for _ in ()
        ).throw(LookupError("Calibration question was not found."))

    @staticmethod
    def _validate_questions(questions: list[CalibrationQuestion]) -> None:
        if [item.category for item in questions] != list(CATEGORIES):
            raise ValueError("Calibration requires EXPERIENCE, MOTIVATION, and PROJECT in order.")
