# Supabase foundation

`migrations/` is the single source of truth for the MVP database schema. Apply
the files in filename order with the Supabase CLI or dashboard migration tools.

The Foundation migration creates only the authenticated user state required by
Milestone 0. Later milestones add schema incrementally when product behavior,
evidence, recovery, or debugging requires persistence.

The root `pnpm test:migrations` command executes the migration against an
ephemeral PostgreSQL-compatible PGlite database with a minimal Supabase Auth
fixture. This keeps Foundation validation local and does not replace validation
against the selected Supabase project before deployment.
