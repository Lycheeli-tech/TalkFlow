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
  create role authenticated;
  create table auth.users (
    id uuid primary key
  );
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

await database.close();
console.log(`Validated ${migrationFiles.length} migration(s) and user provisioning.`);
