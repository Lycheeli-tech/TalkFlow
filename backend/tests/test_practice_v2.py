from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.ai.fakes import FakeSpeechToTextService, FakeTextToSpeechService
from app.api.practice_dependencies import get_practice_service
from app.core.auth import AuthenticatedUser
from app.main import app
from app.practice_v2.answer_service import PracticeService
from app.practice_v2.feedback_service import FakePracticeFeedbackProvider
from app.practice_v2.repository import InMemoryPracticeRepository
from app.practice_v2.selection import QUESTION_BY_ID, select_questions
from app.practice_v2.storage import PracticeAudioStorage


@pytest.fixture
def setup_practice(override_current_user):
    owner = uuid4()
    override_current_user(AuthenticatedUser(id=owner, email="practice@example.test"))
    repo, audio = InMemoryPracticeRepository(), PracticeAudioStorage()
    audio.remote = False
    service = PracticeService(
        repository=repo,
        audio=audio,
        stt=FakeSpeechToTextService("I chose to test the idea with my team."),
        tts=FakeTextToSpeechService(),
        feedback=FakePracticeFeedbackProvider(),
    )
    app.dependency_overrides[get_practice_service] = lambda: service
    return owner, repo, audio, service


@pytest.mark.parametrize("count", [3, 5])
def test_selection_is_static_unique_seeded_and_can_cover_all_questions(count):
    sampled = set()
    for seed in range(120):
        selection = select_questions(count, seed=seed)
        assert selection == select_questions(count, seed=seed)
        assert len(selection) == len(set(selection)) == count
        for question in selection:
            assert question == QUESTION_BY_ID[question.id]
        sampled.update(q.id for q in selection)
    assert sampled == set(QUESTION_BY_ID) and "course-30.follow-up" not in sampled
    for invalid in (0, 1, 4, 6, 59):
        with pytest.raises(ValueError):
            select_questions(invalid)


def start(client, count=3, key="practice-run-key"):
    result = client.post(
        "/api/v1/practice/runs", json={"question_count": count, "idempotency_key": key}
    )
    assert result.status_code == 201
    return result.json()


def submit(client, run, question, key="practice-answer-key"):
    return client.post(
        f"/api/v1/practice/runs/{run['id']}/answers",
        data={"question_id": question, "idempotency_key": key, "duration_ms": 1800},
        files={"recording": ("answer.webm", b"synthetic-contract-audio", "audio/webm")},
    )


@pytest.mark.parametrize("count", [3, 5])
def test_full_interview_pause_skip_return_reanswer_feedback_and_no_history(
    client, setup_practice, count
):
    owner, repo, audio, service = setup_practice
    run = start(client, count)
    base = f"/api/v1/practice/runs/{run['id']}"
    assert start(client, count)["id"] == run["id"]
    assert client.post(base + "/complete").status_code == 409
    assert client.get("/api/v1/practice/runs/current").json()["id"] == run["id"]
    assert (
        client.get(base + "/tts").content
        == f"fake-audio:default:{run['questions'][0]['text']}".encode()
    )
    assert (
        client.patch(base + "/position", json={"position": 0, "paused": True}).json()["status"]
        == "PAUSED"
    )
    assert submit(client, run, run["questions"][0]["id"]).status_code == 409
    assert client.patch(base + "/position", json={"position": 0}).status_code == 200
    first = submit(client, run, run["questions"][0]["id"])
    assert first.status_code == 201
    first_answer = first.json()["answers"][0]
    assert "feedback" not in first.json() and first.json()["current_position"] == 0
    assert "audio_path" not in str(first.json()) and "user_id" not in first.json()
    assert (
        submit(client, run, run["questions"][0]["id"]).json()["answers"][0]["id"]
        == first_answer["id"]
    )
    assert (
        client.get(f"{base}/answers/{first_answer['id']}/audio").content
        == b"synthetic-contract-audio"
    )
    for index in range(1, count):
        skipped = client.patch(base + "/position", json={"position": index, "skip_current": True})
        assert skipped.status_code == 200
    client.patch(base + "/position", json={"position": count - 1, "skip_current": True})
    client.patch(base + "/position", json={"position": 0})
    reanswer = submit(client, run, run["questions"][0]["id"], "reanswer-key").json()
    assert reanswer["answers"][0]["id"] != first_answer["id"]
    feedback = client.post(base + "/complete")
    assert feedback.status_code == 200
    assert (
        feedback.json()["score"] == 95
        and feedback.json()["prompt_version"] == "practice_feedback_v1"
    )
    assert repo.runs == {} and len(repo.cleanup) == 2
    assert len(audio.objects) == 2  # Durable queued cleanup, not deleted before text revocation.
    assert client.get(base).status_code == 404
    assert client.get("/api/v1/practice/runs/current").json() is None
    assert client.post(base + "/complete").status_code == 404
    assert client.delete(base).status_code == 204
    assert client.delete(base).status_code == 204
    assert client.get("/api/v1/practice/history").status_code == 404


def test_api_membership_ownership_validation_and_no_provider_side_effect(
    client, setup_practice, override_current_user
):
    owner, repo, audio, service = setup_practice
    run = start(client)
    base = f"/api/v1/practice/runs/{run['id']}"
    outside = next(q for q in QUESTION_BY_ID if q not in [q["id"] for q in run["questions"]])
    assert submit(client, run, outside).status_code == 404 and not audio.objects
    assert client.patch(base + "/position", json={"position": 4}).status_code == 409
    assert (
        client.post(
            "/api/v1/practice/runs",
            json={"question_count": 3, "idempotency_key": "arbitrary-seed", "seed": 42},
        ).status_code
        == 422
    )
    override_current_user(AuthenticatedUser(id=uuid4(), email="other@example.test"))
    assert client.get(base).status_code == 404
    assert client.get(base + "/tts").status_code == 404
    assert client.post(base + "/complete").status_code == 404
    assert submit(client, run, run["questions"][0]["id"]).status_code == 404
    assert client.delete(base).status_code == 204 and len(repo.runs) == 1


@pytest.mark.asyncio
async def test_expiry_is_fixed_at_creation_pause_does_not_extend_and_deletion_queues_audio(
    setup_practice,
):
    owner, repo, audio, service = setup_practice
    now = datetime(2026, 9, 13, tzinfo=UTC)
    service.clock = lambda: now
    run = await service.create(owner, 3, "expiry-test", seed=4)
    await service.submit(
        owner, run.id, run.question_ids[0], "expiry-answer", b"test", "audio/webm", 1000
    )
    now += timedelta(hours=23)
    paused = await service.position(owner, run.id, 0, True, False)
    assert paused.expires_at == run.created_at + timedelta(hours=24)
    now += timedelta(hours=1)
    with pytest.raises(LookupError):
        await service.get(owner, run.id)
    assert repo.runs == {} and len(repo.cleanup) == 1


@pytest.mark.asyncio
async def test_stt_failure_retries_same_owned_audio_and_cas_prevents_lost_updates(setup_practice):
    owner, repo, audio, service = setup_practice

    class BrokenSTT:
        provider_name = "fault"

        async def transcribe(self, **kwargs):
            raise RuntimeError("fault")

    service.stt = BrokenSTT()
    run = await service.create(owner, 3, "retry-run", seed=1)
    failed = await service.submit(
        owner, run.id, run.question_ids[0], "retry-answer", b"test", "audio/webm", 100
    )
    assert failed.answers[0].status == "FAILED" and failed.answers[0].audio_stored
    service.stt = FakeSpeechToTextService("A true detail.")
    saved = await service.retry(owner, run.id, failed.answers[0].id)
    assert (
        saved.answers[0].id == failed.answers[0].id
        and saved.answers[0].transcript == "A true detail."
    )
    assert len(audio.objects) == 1 and len(saved.answers) == 1
    old = await service.get(owner, run.id)
    await service.position(owner, run.id, 1, False, False)
    with pytest.raises(ValueError):
        await repo.save(old)


@pytest.mark.asyncio
async def test_invalid_feedback_keeps_answers_and_has_bounded_retry(setup_practice):
    owner, repo, audio, service = setup_practice

    class InvalidFeedback(FakePracticeFeedbackProvider):
        async def generate(self, answers):
            result = await super().generate(answers)
            result.strengths[0].quote = "a fabricated quote"
            return result

    run = await service.create(owner, 3, "feedback-run", seed=1)
    run = await service.submit(
        owner, run.id, run.question_ids[0], "feedback-answer", b"test", "audio/webm", 100
    )
    run.skipped = run.question_ids[1:]
    await repo.save(run)
    service.feedback = InvalidFeedback()
    for _ in range(3):
        with pytest.raises(RuntimeError):
            await service.complete(owner, run.id)
        recovered = await service.get(owner, run.id)
        assert recovered.status == "ACTIVE" and recovered.answers[0].status == "SAVED"
    with pytest.raises(ValueError):
        await service.complete(owner, run.id)


@pytest.mark.asyncio
async def test_deleted_during_provider_request_is_never_resurrected(setup_practice):
    owner, repo, audio, service = setup_practice
    run = await service.create(owner, 3, "delete-run", seed=1)

    class DeleteSTT:
        provider_name = "fault"

        async def transcribe(self, **kwargs):
            await repo.remove(owner, run.id)
            return "Late transcript."

    service.stt = DeleteSTT()
    with pytest.raises(LookupError):
        await service.submit(
            owner, run.id, run.question_ids[0], "delete-answer", b"test", "audio/webm", 100
        )
    assert not repo.runs and repo.cleanup


@pytest.mark.asyncio
@pytest.mark.parametrize("lost_response", [False, True])
async def test_upload_finishing_after_abandonment_requeues_deleted_cleanup_job(
    setup_practice, lost_response
):
    owner, repo, audio, service = setup_practice
    run = await service.create(owner, 3, "late-upload-run", seed=1)
    original_store = audio.store

    async def late_store(path, content, content_type):
        await repo.remove(owner, run.id)
        await audio.delete(path)
        repo.cleanup.pop(path)  # Cleanup finished while the upload was in flight.
        await original_store(path, content, content_type)
        if lost_response:
            raise RuntimeError("Upload response was lost.")

    audio.store = late_store
    with pytest.raises(LookupError if lost_response else ValueError):
        await service.submit(
            owner, run.id, run.question_ids[0], "late-upload", b"synthetic", "audio/webm", 1000
        )
    assert not repo.runs and len(repo.cleanup) == len(audio.objects) == 1
    path = next(iter(repo.cleanup))
    assert repo.cleanup[path] == owner
    await audio.delete(path)
    assert not audio.objects


@pytest.mark.asyncio
@pytest.mark.parametrize("transcript", ["", "...", " \n。!? "])
async def test_no_speech_preserves_retryable_audio(setup_practice, transcript):
    owner, repo, audio, service = setup_practice
    service.stt = FakeSpeechToTextService(transcript)
    run = await service.create(owner, 3, "silence-run", seed=1)
    failed = await service.submit(
        owner,
        run.id,
        run.question_ids[0],
        "silence-answer",
        b"synthetic-silence",
        "audio/webm",
        1000,
    )
    assert failed.answers[0].status == "FAILED" and failed.answers[0].audio_stored
    assert failed.answers[0].transcript is None and len(audio.objects) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("late_failure", [False, True])
async def test_late_stt_cannot_overwrite_new_retry(setup_practice, late_failure):
    owner, repo, audio, service = setup_practice
    now = datetime(2026, 9, 13, tzinfo=UTC)
    service.clock = lambda: now
    run = await service.create(owner, 3, "late-run", seed=1)

    class RacingSTT:
        provider_name = "fixture"
        called = False

        async def transcribe(self, **kwargs):
            nonlocal now
            if self.called:
                return "New retry result."
            self.called = True
            now += timedelta(minutes=3)
            active = await service.get(owner, run.id)
            await service.retry(owner, run.id, active.answers[0].id)
            if late_failure:
                raise RuntimeError("late failure")
            return "Old provider result."

    service.stt = RacingSTT()
    saved = await service.submit(
        owner, run.id, run.question_ids[0], "late-answer", b"synthetic", "audio/webm", 1000
    )
    assert saved.answers[0].transcript == "New retry result."
    assert saved.answers[0].status == "SAVED" and len(audio.objects) == 1


@pytest.mark.asyncio
async def test_late_feedback_does_not_delete_or_reset_newer_run(setup_practice):
    owner, repo, audio, service = setup_practice
    run = await service.create(owner, 3, "late-feedback", seed=1)
    run = await service.submit(
        owner, run.id, run.question_ids[0], "feedback-audio", b"synthetic", "audio/webm", 1000
    )
    run.skipped = run.question_ids[1:]
    await repo.save(run)

    class RacingFeedback(FakePracticeFeedbackProvider):
        async def generate(self, answers):
            fresh = await repo.get(owner, run.id)
            fresh.status = "PAUSED"
            await repo.save(fresh)
            return await super().generate(answers)

    service.feedback = RacingFeedback()
    with pytest.raises(ValueError):
        await service.complete(owner, run.id)
    assert (await service.get(owner, run.id)).status == "PAUSED"
