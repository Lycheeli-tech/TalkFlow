"""Apply/check only the approved P8 migration in the configured development database."""

import argparse
import asyncio
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings

SQL = (
    Path(__file__).resolve().parents[2] / "supabase/migrations/202609130021_practice_v2_runs.sql"
).read_text(encoding="utf-8")


async def snapshot(connection):
    users = (
        await connection.execute(
            text(
                "select id,current_day,current_phase,xp,current_streak "
                "from public.users order by id"
            )
        )
    ).all()
    counts = [
        await connection.scalar(text(f"select count(*) from public.{table}"))
        for table in (
            "sessions",
            "attempts",
            "expressions",
            "expression_attempts",
            "retrieval_opportunities",
            "course_answers",
            "memory_items",
        )
    ]
    return users, counts


async def migrate(apply):
    settings = get_settings()
    if settings.app_env == "production":
        raise RuntimeError(
            "This helper is development/test only; production needs a reviewed rollout."
        )
    engine = create_async_engine(settings.database_url)
    try:
        async with engine.connect() as connection:
            transaction = await connection.begin()
            try:
                version = await connection.scalar(
                    text(
                        "select version from supabase_migrations.schema_migrations "
                        "where version='202609130021'"
                    )
                )
                if version:
                    print("P8 already applied/registered; no mutation.")
                    return
                before = await snapshot(connection)
                raw = await connection.get_raw_connection()
                await raw.driver_connection.execute(SQL)
                assert await snapshot(connection) == before
                if apply:
                    await connection.execute(
                        text(
                            "insert into supabase_migrations.schema_migrations"
                            "(version,name,statements) "
                            "values (:version,:name,:statements)"
                        ),
                        {
                            "version": "202609130021",
                            "name": "practice_v2_runs",
                            "statements": [SQL],
                        },
                    )
                    await transaction.commit()
                    print("P8 applied/registered; Legacy/Course/Memory snapshots unchanged.")
                else:
                    print("P8 migration dry-run passed; transaction rolled back.")
            finally:
                if transaction.is_active:
                    await transaction.rollback()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    asyncio.run(migrate(args.apply))
