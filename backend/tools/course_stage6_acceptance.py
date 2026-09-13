"""Explicit test-environment P6 migration and disposable real-service acceptance helper.

No credentials or learner content are printed. State is stored in the OS temporary directory.
"""

import argparse
import asyncio
import json
import secrets
import tempfile
from pathlib import Path
from uuid import UUID, uuid4

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import get_settings
from app.course.repository import SQLCourseAnswerRepository
from app.course.storage import build_course_audio_storage

MIGRATION_PATH = (
    Path(__file__).resolve().parents[2]
    / "supabase/migrations/202609130020_chinese_answer_drafts.sql"
)
MIGRATION_SQL = MIGRATION_PATH.read_text(encoding="utf-8")
LEGACY_TABLES = (
    "sessions",
    "attempts",
    "expressions",
    "expression_attempts",
    "retrieval_opportunities",
)


async def snapshot(connection):
    users = (
        await connection.execute(
            text(
                "select id, current_day, current_phase, xp, current_streak "
                "from public.users order by id"
            )
        )
    ).all()
    counts = [
        await connection.scalar(text(f"select count(*) from public.{table}"))
        for table in LEGACY_TABLES
    ]
    return [tuple(str(value) for value in row) for row in users], counts


async def migrate(apply):
    engine = create_async_engine(get_settings().database_url)
    try:
        async with engine.begin() as connection:
            columns = (
                (
                    await connection.execute(
                        text(
                            "select column_name from information_schema.columns "
                            "where table_schema='supabase_migrations' "
                            "and table_name='schema_migrations'"
                        )
                    )
                )
                .scalars()
                .all()
            )
            versions = (
                (
                    await connection.execute(
                        text(
                            "select version from supabase_migrations.schema_migrations "
                            "order by version"
                        )
                    )
                )
                .scalars()
                .all()
            )
            print("Migration registry columns:", columns)
            print("Applied versions:", versions)
            if not apply:
                return
            if "202609130020" in versions:
                print("P6 already registered; no mutation.")
                return
            if "202609120019" not in versions:
                raise RuntimeError("Expected P4/P5 test baseline was not registered.")
            before = await snapshot(connection)
            raw = await connection.get_raw_connection()
            await raw.driver_connection.execute(MIGRATION_SQL)
            await connection.execute(
                text(
                    "insert into supabase_migrations.schema_migrations (version, name, statements) "
                    "values (:version, :name, :statements)"
                ),
                {
                    "version": "202609130020",
                    "name": "chinese_answer_drafts",
                    "statements": [MIGRATION_SQL],
                },
            )
            if await snapshot(connection) != before:
                raise RuntimeError("Legacy snapshot changed; rolling back P6 migration.")
            print(
                "P6 migration applied/registered; all Legacy progress and table counts unchanged."
            )
    finally:
        await engine.dispose()


async def prepare(*, generate_audio=True):
    settings = get_settings()
    state = {
        "email": f"fluentloop-p6-{uuid4().hex[:12]}@outlook.com",
        "password": secrets.token_urlsafe(24),
    }
    state_path = Path(tempfile.gettempdir()) / f"fluentloop-p6-{uuid4().hex}.json"
    headers = {
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
        "apikey": settings.supabase_service_role_key,
    }
    async with httpx.AsyncClient(timeout=90) as client:
        response = await client.post(
            settings.supabase_url + "/auth/v1/admin/users",
            headers=headers,
            json={"email": state["email"], "password": state["password"], "email_confirm": True},
        )
        response.raise_for_status()
        state["user_id"] = response.json()["id"]
        state_path.write_text(json.dumps(state), encoding="utf-8")
        response = await client.post(
            settings.supabase_url + "/auth/v1/token?grant_type=password",
            headers=headers,
            json={"email": state["email"], "password": state["password"]},
        )
        response.raise_for_status()
        state["access_token"] = response.json()["access_token"]
        state_path.write_text(json.dumps(state), encoding="utf-8")
        if not generate_audio:
            print("Disposable confirmed P6 device account state:", state_path)
            print("Password sign-in verified; no synthetic audio generated.")
            return
        response = await client.post(
            settings.bailian_dashscope_base_url.rstrip("/")
            + "/services/aigc/multimodal-generation/generation",
            headers={"Authorization": f"Bearer {settings.bailian_api_key}"},
            json={
                "model": settings.bailian_tts_model,
                "input": {
                    "text": "这是合成测试。我在一个练习项目中负责测试，没有负责整个项目。",
                    "voice": settings.bailian_tts_voice,
                    "language_type": "Chinese",
                },
            },
        )
        response.raise_for_status()
        audio_response = await client.get(response.json()["output"]["audio"]["url"])
        audio_response.raise_for_status()
        audio_path = state_path.with_suffix(".wav")
        audio_path.write_bytes(audio_response.content)
        state["audio_path"] = str(audio_path)
        state_path.write_text(json.dumps(state), encoding="utf-8")
    print("Disposable P6 state:", state_path)


async def submit(state_path, confirm=False):
    state = json.loads(state_path.read_text(encoding="utf-8"))
    async with httpx.AsyncClient(timeout=240, trust_env=False) as client:
        response = await client.post(
            "http://127.0.0.1:8000/api/v1/courses/course-11/questions/course-11.core/answers",
            headers={"Authorization": "Bearer " + state["access_token"]},
            data={
                "answer_language": "CHINESE",
                "idempotency_key": "p6-real-" + uuid4().hex,
                "response_duration_ms": "8000",
            },
            files={
                "recording": (
                    "synthetic.wav",
                    await asyncio.to_thread(Path(state["audio_path"]).read_bytes),
                    "audio/wav",
                )
            },
        )
        response.raise_for_status()
        answer = response.json()
        state.setdefault("answer_ids", []).append(answer["id"])
        state["last_answer_id"] = answer["id"]
        state_path.write_text(json.dumps(state), encoding="utf-8")
        print(
            "Real Chinese upload status:", answer["status"], "error:", answer["provider_error_code"]
        )
        if answer["status"] != "AWAITING_CONFIRMATION":
            raise RuntimeError("Real Chinese Draft was not ready.")
        assert answer["transcript"]["source_language"] == "CHINESE"
        assert any("\u4e00" <= char <= "\u9fff" for char in answer["transcript"]["transcript"])
        assert answer["transcript"]["organized_english"]
        history = await client.get(
            "http://127.0.0.1:8000/api/v1/courses/course-11/questions/course-11.core/history",
            headers={"Authorization": "Bearer " + state["access_token"]},
        )
        assert answer["id"] not in [item["id"] for item in history.json()["answers"]]
        if confirm:
            target = "http://127.0.0.1:8000/api/v1/course-answers/" + answer["id"] + "/confirm"
            response = await client.post(
                target, headers={"Authorization": "Bearer " + state["access_token"]}
            )
            response.raise_for_status()
            assert response.json()["status"] == "SAVED"
            repeat = await client.post(
                target, headers={"Authorization": "Bearer " + state["access_token"]}
            )
            assert repeat.json()["id"] == answer["id"] and repeat.json()["status"] == "SAVED"
            print("Real confirmation + idempotent repeat: passed.")


async def cleanup(state_path):
    state = json.loads(state_path.read_text(encoding="utf-8"))
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    try:
        async with engine.connect() as connection:
            answer_rows = (
                await connection.execute(
                    text("select id, audio_path from public.course_answers where user_id=:owner"),
                    {"owner": state["user_id"]},
                )
            ).all()
    finally:
        await engine.dispose()
    async with httpx.AsyncClient(timeout=90, trust_env=False) as client:
        audio = build_course_audio_storage()
        for answer_id, path in answer_rows:
            if path is not None:
                await audio.delete(path=path)
            response = await client.delete(
                "http://127.0.0.1:8000/api/v1/course-answers/" + str(answer_id),
                headers={"Authorization": "Bearer " + state["access_token"]},
            )
            if response.status_code not in {204, 404}:
                response.raise_for_status()
    async with httpx.AsyncClient(timeout=90) as client:
        response = await client.delete(
            settings.supabase_url + "/auth/v1/admin/users/" + state["user_id"],
            headers={
                "Authorization": f"Bearer {settings.supabase_service_role_key}",
                "apikey": settings.supabase_service_role_key,
            },
        )
        response.raise_for_status()
    engine = create_async_engine(settings.database_url)
    try:
        async with engine.connect() as connection:
            assert not await connection.scalar(
                text(
                    "select count(*) from storage.objects "
                    "where bucket_id='learner-audio' and name like :prefix"
                ),
                {"prefix": state["user_id"] + "/%"},
            )
            assert not await connection.scalar(
                text("select count(*) from public.course_answers where user_id=:owner"),
                {"owner": state["user_id"]},
            )
            print("Disposable persisted Answer and private Storage object counts: zero.")
    finally:
        await engine.dispose()
    audio_path = Path(state.get("audio_path", str(state_path.with_suffix(".wav"))))
    await asyncio.to_thread(audio_path.unlink, missing_ok=True)
    state_path.unlink()
    print("Disposable Auth user, Answer data, local credentials, and synthetic audio removed.")


async def inspect(state_path):
    state = json.loads(state_path.read_text(encoding="utf-8"))
    engine = create_async_engine(get_settings().database_url)
    try:
        async with engine.connect() as connection:
            current = await snapshot(connection)
            baseline = state.get("legacy_snapshot")
            if baseline is not None:
                assert json.loads(json.dumps(current)) == baseline
                print("Real-service Legacy field/table snapshot: unchanged.")
            state["legacy_snapshot"] = current
            rows = (
                await connection.execute(
                    text(
                        "select a.status, a.audio_retention_status, a.audio_cleanup_pending, "
                        "(a.audio_path is null), t.stt_provider, "
                        "t.organizer_provider, t.fidelity_prompt_version "
                        "from public.course_answers a left join public.course_transcripts t "
                        "on t.answer_id=a.id where a.user_id=:owner order by a.created_at"
                    ),
                    {"owner": state["user_id"]},
                )
            ).all()
            print(
                "Synthetic Answer status/retention/provider/prompts:", [tuple(row) for row in rows]
            )
            state_path.write_text(json.dumps(state), encoding="utf-8")
    finally:
        await engine.dispose()


async def retry_cleanup(state_path):
    state = json.loads(state_path.read_text(encoding="utf-8"))
    owner = UUID(state["user_id"])
    engine = create_async_engine(get_settings().database_url)
    try:
        async with AsyncSession(engine, expire_on_commit=False) as session:
            pending = (
                await session.execute(
                    text(
                        "select id, audio_path from public.course_answers "
                        "where user_id=:owner and audio_cleanup_pending"
                    ),
                    {"owner": owner},
                )
            ).all()
            audio = build_course_audio_storage()
            repo = SQLCourseAnswerRepository(session)
            for answer_id, path in pending:
                if path is not None:
                    await audio.delete(path=path)
                await repo.mark_cleanup_complete(owner, answer_id)
            print("Disposable owner-scoped real cleanup retries completed:", len(pending))
    finally:
        await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "action",
        choices=[
            "check",
            "migrate",
            "prepare",
            "prepare-device",
            "submit",
            "confirm",
            "inspect",
            "retry-cleanup",
            "cleanup",
        ],
    )
    parser.add_argument("--state", type=Path)
    args = parser.parse_args()
    if args.action in {"check", "migrate"}:
        asyncio.run(migrate(args.action == "migrate"))
    elif args.action in {"prepare", "prepare-device"}:
        asyncio.run(prepare(generate_audio=args.action == "prepare"))
    elif args.action in {"submit", "confirm"}:
        asyncio.run(submit(args.state, args.action == "confirm"))
    elif args.action == "inspect":
        asyncio.run(inspect(args.state))
    elif args.action == "retry-cleanup":
        asyncio.run(retry_cleanup(args.state))
    else:
        asyncio.run(cleanup(args.state))
