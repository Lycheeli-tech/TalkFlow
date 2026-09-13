"""Owner-scoped synthetic speech acceptance; never prints transcripts/credentials."""

import argparse
import asyncio
import json
from pathlib import Path
from uuid import UUID, uuid4

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.api.core_dependencies import get_course_tts_service
from app.api.practice_dependencies import get_practice_audio
from app.core.config import get_settings
from app.practice_v2.cleanup import cleanup_once
from app.practice_v2.repository import SQLPracticeRepository


async def snapshot(connection, owner):
    progress = (
        await connection.execute(
            text(
                "select current_day,current_phase,xp,current_streak "
                "from public.users where id=:owner"
            ),
            {"owner": owner},
        )
    ).all()
    counts = [
        await connection.scalar(
            text(f"select count(*) from public.{table} where user_id=:owner"), {"owner": owner}
        )
        for table in (
            "sessions",
            "attempts",
            "expressions",
            "expression_attempts",
            "retrieval_opportunities",
            "course_answers",
            "memory_items",
            "memory_sources",
        )
    ]
    return progress, counts


async def smoke(state_path, base_url, count, prepare=False):
    state = json.loads(state_path.read_text(encoding="utf-8"))
    owner = UUID(state["user_id"])
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    run_id = None
    keep_run = False
    try:
        async with engine.connect() as connection:
            before = await snapshot(connection, owner)
        speech = await get_course_tts_service().synthesize(
            text=(
                "This is a synthetic acceptance recording. I tested an idea with my team "
                "and explained what I learned."
            ),
            voice="default",
        )
        async with httpx.AsyncClient(timeout=60) as auth_client:
            login = await auth_client.post(
                f"{settings.supabase_url}/auth/v1/token?grant_type=password",
                headers={"apikey": settings.supabase_service_role_key},
                json={"email": state["email"], "password": state["password"]},
            )
            login.raise_for_status()
        async with httpx.AsyncClient(timeout=150, trust_env=False) as client:
            headers = {"Authorization": "Bearer " + login.json()["access_token"]}
            base = base_url.rstrip("/") + "/api/v1/practice/runs"
            result = await client.post(
                base,
                headers=headers,
                json={"question_count": count, "idempotency_key": "p8-live-" + uuid4().hex},
            )
            result.raise_for_status()
            run = result.json()
            run_id = run["id"]
            run_base = base + "/" + run_id
            question = run["questions"][0]["id"]
            response = await client.post(
                run_base + "/answers",
                headers=headers,
                data={
                    "question_id": question,
                    "duration_ms": 6500,
                    "idempotency_key": "p8-live-answer-" + uuid4().hex,
                },
                files={"recording": ("synthetic.wav", speech, "audio/wav")},
            )
            response.raise_for_status()
            saved = response.json()
            assert saved["answers"][0]["status"] == "SAVED"
            playback = await client.get(
                run_base + "/answers/" + saved["answers"][0]["id"] + "/audio", headers=headers
            )
            playback.raise_for_status()
            assert playback.content == speech
            assert client and saved["current_position"] == 0 and "feedback" not in saved
            for index in range(1, count):
                position = await client.patch(
                    run_base + "/position",
                    headers=headers,
                    json={"position": index, "skip_current": index != 1},
                )
                position.raise_for_status()
            last = await client.patch(
                run_base + "/position",
                headers=headers,
                json={"position": count - 1, "skip_current": True},
            )
            last.raise_for_status()
            if prepare:
                keep_run = True
                state["p8_run_id"] = run_id
                state_path.write_text(json.dumps(state), encoding="utf-8")
                print("Synthetic voiced Practice Run ready for UI completion:", run_id)
                return
            feedback = await client.post(run_base + "/complete", headers=headers)
            feedback.raise_for_status()
            assert feedback.json()["provider_name"] == "bailian"
            assert feedback.json()["prompt_version"] == "practice_feedback_v1"
            assert (await client.get(run_base, headers=headers)).status_code == 404
            print(
                "Real P8",
                count,
                "question run: TTS/upload/STT/audio/whole-feedback passed; score",
                feedback.json()["score"],
                "; completed Run unavailable.",
            )
        async with engine.connect() as connection:
            assert await snapshot(connection, owner) == before
        print("Legacy/Course/Memory owner snapshot unchanged.")
    finally:
        from sqlalchemy.ext.asyncio import AsyncSession

        async with AsyncSession(engine, expire_on_commit=False) as session:
            if run_id and not keep_run:
                await SQLPracticeRepository(session).remove(owner, UUID(run_id))
            await cleanup_once(session, get_practice_audio(), owner=owner)
            left = await session.scalar(
                text(
                    "select count(*) from public.practice_audio_cleanup_jobs where user_id=:owner"
                ),
                {"owner": owner},
            )
            print("Owner pending Practice audio cleanup:", left)
        await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--count", type=int, choices=(3, 5), default=3)
    parser.add_argument("--prepare", action="store_true")
    args = parser.parse_args()
    asyncio.run(smoke(args.state, args.base_url, args.count, args.prepare))
