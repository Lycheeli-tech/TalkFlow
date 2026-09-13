from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile

from app.api.core_dependencies import get_course_current_user
from app.api.practice_dependencies import get_practice_service
from app.core.config import get_settings
from app.practice_v2.schemas import CreateRun, PositionUpdate
from app.practice_v2.selection import QUESTION_BY_ID

router = APIRouter()


def view(run):
    if run is None:
        return None
    return {
        "id": run.id,
        "question_count": len(run.question_ids),
        "questions": [QUESTION_BY_ID[q] for q in run.question_ids],
        "current_position": run.current_position,
        "status": run.status,
        "expires_at": run.expires_at,
        "skipped": run.skipped,
        "answers": [
            {
                "id": a.id,
                "question_id": a.question_id,
                "status": a.status,
                "transcript": a.transcript,
                "duration_ms": a.duration_ms,
                "audio_available": a.audio_stored,
                "error_code": a.error_code,
            }
            for q in run.question_ids
            if (a := run.latest(q))
        ],
    }


async def call(operation):
    try:
        return await operation
    except LookupError as error:
        raise HTTPException(404, "Practice resource was not found.") from error
    except ValueError as error:
        raise HTTPException(409, str(error)) from error
    except RuntimeError as error:
        raise HTTPException(503, str(error)) from error


@router.post("/runs", status_code=201)
async def create(
    body: CreateRun, user=Depends(get_course_current_user), service=Depends(get_practice_service)
):
    return view(await call(service.create(user.id, body.question_count, body.idempotency_key)))


@router.get("/runs/current")
async def current(user=Depends(get_course_current_user), service=Depends(get_practice_service)):
    return view(await call(service.current(user.id)))


@router.get("/runs/{run_id}")
async def get(
    run_id: UUID, user=Depends(get_course_current_user), service=Depends(get_practice_service)
):
    return view(await call(service.get(user.id, run_id)))


@router.patch("/runs/{run_id}/position")
async def position(
    run_id: UUID,
    body: PositionUpdate,
    user=Depends(get_course_current_user),
    service=Depends(get_practice_service),
):
    return view(
        await call(service.position(user.id, run_id, body.position, body.paused, body.skip_current))
    )


@router.post("/runs/{run_id}/answers", status_code=201)
async def answer(
    run_id: UUID,
    question_id: Annotated[str, Form(max_length=64)],
    idempotency_key: Annotated[str, Form(min_length=8, max_length=128)],
    duration_ms: Annotated[int, Form(ge=0)],
    recording: UploadFile = File(...),
    user=Depends(get_course_current_user),
    service=Depends(get_practice_service),
):
    content = await recording.read(get_settings().max_audio_bytes + 1)
    if not content:
        raise HTTPException(422, "Recording cannot be empty.")
    if len(content) > get_settings().max_audio_bytes:
        raise HTTPException(413, "Recording is too large.")
    if not (recording.content_type or "").startswith("audio/"):
        raise HTTPException(415, "An audio recording is required.")
    return view(
        await call(
            service.submit(
                user.id,
                run_id,
                question_id,
                idempotency_key,
                content,
                recording.content_type,
                duration_ms,
            )
        )
    )


@router.post("/runs/{run_id}/answers/{answer_id}/retry")
async def retry(
    run_id: UUID,
    answer_id: UUID,
    user=Depends(get_course_current_user),
    service=Depends(get_practice_service),
):
    return view(await call(service.retry(user.id, run_id, answer_id)))


@router.get("/runs/{run_id}/answers/{answer_id}/audio")
async def audio(
    run_id: UUID,
    answer_id: UUID,
    user=Depends(get_course_current_user),
    service=Depends(get_practice_service),
):
    content, content_type = await call(service.answer_audio(user.id, run_id, answer_id))
    return Response(content, media_type=content_type)


@router.get("/runs/{run_id}/tts")
async def tts(
    run_id: UUID, user=Depends(get_course_current_user), service=Depends(get_practice_service)
):
    return Response(await call(service.question_audio(user.id, run_id)), media_type="audio/mpeg")


@router.post("/runs/{run_id}/complete")
async def complete(
    run_id: UUID, user=Depends(get_course_current_user), service=Depends(get_practice_service)
):
    return await call(service.complete(user.id, run_id))


@router.delete("/runs/{run_id}", status_code=204)
async def delete(
    run_id: UUID, user=Depends(get_course_current_user), service=Depends(get_practice_service)
):
    await service.repo.remove(user.id, run_id)
    return Response(status_code=204)
