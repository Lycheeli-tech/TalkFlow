# FluentLoop

FluentLoop turns English that a learner understands into language they can
retrieve and use independently in interview conditions. The repository remains
named `TalkFlow`; the product display name is **FluentLoop**.

This repository is being built milestone by milestone from the approved MVP
specification. V1.5 and V2 features are intentionally out of scope.

## Foundation development

Prerequisites:

- Node.js 22 or newer and pnpm
- Python 3.12
- A Supabase project, or the Supabase local development stack

Setup:

1. Copy `.env.example` to `.env` and provide local development values.
2. Run `pnpm install` at the repository root.
3. Create and activate a Python environment, then install the backend with its development extras:

   ```text
   python -m venv backend/.venv
   backend/.venv/Scripts/activate      # Windows
   source backend/.venv/bin/activate   # macOS/Linux
   python -m pip install -e "backend[dev]"
   ```
4. Apply the SQL files in `supabase/migrations` to the Supabase database.
5. Start the API from `backend` with `uvicorn app.main:app --reload`.
6. Start the web app with `pnpm dev`.

Useful checks:

```text
pnpm lint
pnpm typecheck
pnpm build
pnpm test:migrations
python -m pytest backend/tests
ruff check backend
```

The first live LLM, speech-to-text, and text-to-speech providers will be chosen
in the milestone that needs them. Foundation uses deterministic fake providers.

For local deterministic development, keep the provider settings in `.env` at
`fake`. Real Supabase/OpenAI credentials are required only for the later live
integration gate; never expose server-only keys through `NEXT_PUBLIC_*` values.
