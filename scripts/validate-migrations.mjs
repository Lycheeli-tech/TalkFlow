import { readdir, readFile } from "node:fs/promises";
import path from "node:path";
import process from "node:process";

import { PGlite } from "@electric-sql/pglite";

const repositoryRoot = path.resolve(import.meta.dirname, "..");
const migrationsDirectory = path.join(repositoryRoot, "supabase", "migrations");
const migrationFiles = (await readdir(migrationsDirectory))
  .filter((file) => file.endsWith(".sql"))
  .sort();

if (migrationFiles.length === 0) {
  throw new Error("No Supabase migrations were found.");
}

const database = new PGlite();

await database.exec(`
  create schema if not exists auth;
  create schema if not exists storage;
  create role authenticated;
  create role service_role;
  create table auth.users (
    id uuid primary key
  );
  create table storage.buckets (
    id text primary key,
    name text not null,
    public boolean not null default false
  );
  create table storage.objects (
    id uuid primary key default gen_random_uuid(),
    bucket_id text not null references storage.buckets (id),
    name text not null
  );
  alter table storage.objects enable row level security;
  create function auth.uid()
  returns uuid
  language sql
  stable
  as $$
    select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid
  $$;
`);

for (const file of migrationFiles) {
  const migration = await readFile(path.join(migrationsDirectory, file), "utf8");
  await database.exec(migration);
}

const userId = "11111111-1111-4111-8111-111111111111";
await database.query("insert into auth.users (id) values ($1)", [userId]);
const result = await database.query(
  "select id, interface_language, support_language from public.users where id = $1",
  [userId],
);

if (result.rows.length !== 1) {
  throw new Error("Foundation migration did not provision the user row.");
}

const expectedRlsTables = [
  "about_me_profiles",
  "attempts",
  "course_answers",
  "course_audio_cleanup_jobs",
  "course_feedback",
  "course_transcripts",
  "document_cleanup_jobs",
  "error_patterns",
  "expression_attempts",
  "expressions",
  "learner_assessments",
  "memory_items",
  "memory_sources",
  "profiles",
  "retrieval_opportunities",
  "sessions",
  "source_documents",
  "stories",
  "target_roles",
  "users",
];
const rlsResult = await database.query(
  `select tablename
   from pg_tables
   where schemaname = 'public' and rowsecurity = true
   order by tablename`,
);
const rlsTables = rlsResult.rows.map((row) => row.tablename);
if (JSON.stringify(rlsTables) !== JSON.stringify(expectedRlsTables)) {
  throw new Error(`Unexpected RLS coverage: ${rlsTables.join(", ")}`);
}

await database.close();
console.log(`Validated ${migrationFiles.length} migration(s) and user provisioning.`);
