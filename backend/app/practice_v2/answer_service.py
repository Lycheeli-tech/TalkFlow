import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from app.ai.interfaces import SpeechToTextService, TextToSpeechService
from app.practice_v2.feedback_service import PROMPT_VERSION, PracticeFeedbackProvider
from app.practice_v2.repository import PracticeRepository
from app.practice_v2.schemas import Attempt, Feedback, Run
from app.practice_v2.selection import QUESTION_BY_ID, select_questions
from app.practice_v2.storage import PracticeAudioStorage

RUN_TTL = timedelta(hours=24)  # Approved ADR-032; fixed from creation.
PROCESSING_LEASE = timedelta(minutes=2)
MAX_RETRIES = 3
logger = logging.getLogger(__name__)


class PracticeService:
    def __init__(
        self,
        *,
        repository: PracticeRepository,
        audio: PracticeAudioStorage,
        stt: SpeechToTextService,
        tts: TextToSpeechService,
        feedback: PracticeFeedbackProvider,
        clock=None,
    ):
        self.repo, self.audio, self.stt, self.tts, self.feedback = (
            repository,
            audio,
            stt,
            tts,
            feedback,
        )
        self.clock = clock or (lambda: datetime.now(UTC))

    async def create(self, owner, count, key, *, seed=None):
        existing = await self.repo.find_key(owner, key)
        if existing:
            run = await self.get(owner, existing.id)
            if len(run.question_ids) != count:
                raise ValueError("Idempotency key belongs to a different Practice request.")
            return run
        now = self.clock()
        return await self.repo.create(
            Run(
                id=uuid4(),
                user_id=owner,
                idempotency_key=key,
                question_ids=[q.id for q in select_questions(count, seed=seed)],
                created_at=now,
                updated_at=now,
                expires_at=now + RUN_TTL,
            )
        )

    async def get(self, owner: UUID, run_id: UUID) -> Run:
        run = await self.repo.get(owner, run_id)
        if run and run.expires_at <= self.clock():
            await self.repo.remove(owner, run_id)
            run = None
        if run is None:
            raise LookupError("Practice Run was not found.")
        return run

    async def current(self, owner):
        run = await self.repo.current(owner)
        if run is None:
            return None
        try:
            return await self.get(owner, run.id)
        except LookupError:
            return None

    def require_idle(self, run):
        if run.status == "GENERATING" and self.clock() - run.updated_at < PROCESSING_LEASE:
            raise ValueError("Whole-interview feedback is being generated.")
        if run.status == "GENERATING":
            run.status = "ACTIVE"  # A crashed generation lease can be recovered deterministically.
        if any(
            a.status == "PROCESSING" and self.clock() - a.updated_at < PROCESSING_LEASE
            for a in run.answers
        ):
            raise ValueError("The recording is being processed. Wait before navigating.")

    async def position(self, owner, run_id, position, paused, skip_current):
        run = await self.get(owner, run_id)
        self.require_idle(run)
        if position >= len(run.question_ids):
            raise ValueError("Position is outside this Practice Run.")
        if skip_current:
            question_id = run.question_ids[run.current_position]
            if question_id not in run.skipped:
                run.skipped.append(question_id)
        run.current_position, run.status, run.updated_at = (
            position,
            "PAUSED" if paused else "ACTIVE",
            self.clock(),
        )
        return await self.repo.save(run)

    async def submit(self, owner, run_id, question_id, key, content, content_type, duration_ms):
        run = await self.get(owner, run_id)
        if question_id not in run.question_ids:
            raise LookupError("Question was not found in this Practice Run.")
        existing = next((a for a in run.answers if a.idempotency_key == key), None)
        if existing:
            if existing.question_id != question_id:
                raise ValueError("Idempotency target does not match.")
            if existing.status == "SAVED":
                return run
            return await self.retry(owner, run_id, existing.id, content)
        self.require_idle(run)
        if run.status == "PAUSED" or run.question_ids[run.current_position] != question_id:
            raise ValueError("Resume and select this question before answering.")
        attempt_id = uuid4()
        attempt = Attempt(
            id=attempt_id,
            question_id=question_id,
            idempotency_key=key,
            audio_path=self.audio.path(owner, run.id, attempt_id),
            content_type=content_type,
            duration_ms=duration_ms,
            updated_at=self.clock(),
        )
        run.answers.append(attempt)
        run.updated_at = self.clock()
        run = await self.repo.save(run)  # Persist ownership before any provider or upload.
        return await self.process(run, attempt.id, content)

    async def retry(self, owner, run_id, attempt_id, content=None):
        run = await self.get(owner, run_id)
        attempt = next((a for a in run.answers if a.id == attempt_id), None)
        if attempt is None:
            raise LookupError("Practice recording was not found.")
        if attempt.status == "SAVED":
            return run
        self.require_idle(run)
        if attempt.retries >= MAX_RETRIES:
            raise ValueError("Retry limit reached. Record a new answer.")
        attempt.retries += 1
        attempt.status, attempt.updated_at = "PROCESSING", self.clock()
        run.updated_at = self.clock()
        run = await self.repo.save(run)
        return await self.process(run, attempt_id, content)

    async def process(self, run, attempt_id, content):
        attempt = next(a for a in run.answers if a.id == attempt_id)
        processing_stamp = attempt.updated_at
        try:
            if not attempt.audio_stored:
                if not content:
                    raise RuntimeError("Recording upload must be retried.")
                await self.audio.store(attempt.audio_path, content, attempt.content_type)
                attempt.audio_stored = True
                run = await self.repo.save(run)
                attempt = next(a for a in run.answers if a.id == attempt_id)
            transcript = await self.stt.transcribe(
                audio=await self.audio.load(attempt.audio_path), content_type=attempt.content_type
            )
            if not any(character.isalnum() for character in transcript):
                raise RuntimeError("No speech was detected.")
            # Reload after provider work: expired/deleted Runs must never be resurrected.
            run = await self.get(run.user_id, run.id)
            attempt = next(a for a in run.answers if a.id == attempt_id)
            if attempt.updated_at != processing_stamp or attempt.status != "PROCESSING":
                return run
            attempt.transcript = transcript.strip()[:20000]
            attempt.stt_provider = self.stt.provider_name
            attempt.stt_model = getattr(self.stt, "model_name", None)
            attempt.status, attempt.error_code = "SAVED", None
            run.skipped = [q for q in run.skipped if q != attempt.question_id]
        except (LookupError, ValueError):
            if await self.repo.get(run.user_id, run.id) is None:
                # Deletion cleanup may have finished before an in-flight upload did.
                await self.repo.queue_audio_cleanup(run.user_id, attempt.audio_path)
            raise
        except Exception:
            if await self.repo.get(run.user_id, run.id) is None:
                await self.repo.queue_audio_cleanup(run.user_id, attempt.audio_path)
                raise LookupError("Practice Run was not found.") from None
            run = await self.get(run.user_id, run.id)
            attempt = next(a for a in run.answers if a.id == attempt_id)
            if attempt.updated_at != processing_stamp or attempt.status != "PROCESSING":
                return run
            attempt.status, attempt.error_code = "FAILED", "PRACTICE_PROCESSING_FAILED"
        attempt.updated_at, run.updated_at = self.clock(), self.clock()
        return await self.repo.save(run)

    async def question_audio(self, owner, run_id):
        run = await self.get(owner, run_id)
        return await self.tts.synthesize(
            text=QUESTION_BY_ID[run.question_ids[run.current_position]].text, voice="default"
        )

    async def answer_audio(self, owner, run_id, attempt_id):
        run = await self.get(owner, run_id)
        attempt = next((a for a in run.answers if a.id == attempt_id and a.audio_stored), None)
        if attempt is None:
            raise LookupError("Practice recording was not found.")
        return await self.audio.load(attempt.audio_path), attempt.content_type

    async def complete(self, owner, run_id):
        run = await self.get(owner, run_id)
        self.require_idle(run)
        final = [run.latest(q) for q in run.question_ids]
        if any(
            (a is None or a.status != "SAVED") and q not in run.skipped
            for q, a in zip(run.question_ids, final, strict=True)
        ):
            raise ValueError("Answer or skip every question before ending the interview.")
        evidence = {a.question_id: a.transcript for a in final if a and a.status == "SAVED"}
        if not evidence:
            raise ValueError("Record at least one answer before requesting feedback.")
        if run.feedback_retries >= MAX_RETRIES:
            raise ValueError(
                "Feedback retry limit reached. Your recordings remain available until expiry."
            )
        run.status, run.updated_at = "GENERATING", self.clock()
        run.feedback_retries += 1
        run = await self.repo.save(run)
        try:
            generated = await self.feedback.generate(
                [
                    {"question_id": q, "question": QUESTION_BY_ID[q].text, "transcript": t}
                    for q, t in evidence.items()
                ]
            )
            for item in (*generated.strengths, *generated.improvements):
                if item.question_id not in evidence or item.quote not in evidence[item.question_id]:
                    raise RuntimeError("Feedback evidence does not match this interview.")
            fresh = await self.get(owner, run_id)
            if fresh.revision != run.revision:
                raise ValueError("Practice changed while generating feedback. Reload and retry.")
        except Exception as error:
            logger.warning("practice_feedback_failed: %s", type(error).__name__)
            fresh = await self.get(owner, run_id)
            if fresh.revision != run.revision:
                raise ValueError(
                    "Practice changed while generating feedback. Reload and retry."
                ) from error
            run = fresh
            run.status, run.updated_at = "ACTIVE", self.clock()
            await self.repo.save(run)
            raise RuntimeError(
                "Feedback unavailable. Your answers are preserved; retry ending the interview."
            ) from error
        feedback = Feedback(
            **generated.model_dump(),
            prompt_version=PROMPT_VERSION,
            provider_name=self.feedback.provider_name,
            model_name=self.feedback.model_name,
        )
        await self.repo.remove(owner, run_id, expected_revision=run.revision)
        return feedback  # No completed Run/Transcript/Feedback exists after this response.
