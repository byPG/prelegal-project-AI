# Prelegal — project documentation

## What it is

Prelegal is a SaaS app where users generate legal agreements from ready-made templates stored in the `templates` directory. The field-filling process happens through a conversation with an AI assistant — it's the assistant that figures out which document is needed and what data should go into it.

The full list of supported documents lives in `catalog.json` at the repo root:

@catalog.json

All 11 document types are supported; full user authentication and document persistence are still targets — see **Implementation status** at the end of this file for what's actually built so far.

## How feature work happens

1. Pull the feature requirements from Jira (Atlassian tools).
2. Implement the feature, following all 7 steps of the feature-dev process — none get skipped.
3. Write unit and integration tests, verify behavior thoroughly, and fix any bugs found.
4. Open a PR via the GitHub tools.

## AI layer

For talking to language models, use LiteLLM through OpenRouter, calling `openrouter/openrouter/free` — OpenRouter's own adaptive "Free Models Router", which picks whichever free model is currently live and capable of what the request needs (structured output, tool calling, ...). No separate inference provider needs to be configured — it's free (rate-limited to 20 requests/min and 200 requests/day, no credit card required). Responses should use Structured Outputs so they can be parsed easily and used to populate document fields.

**Do not pin a specific `:free` model slug** (e.g. `openai/gpt-oss-120b:free`) as the primary/only model. This was tried first and rotted away within hours — OpenRouter pulled or repriced that specific free slug with no warning, exactly the volatility this section used to only warn about in the abstract. The adaptive router above is self-healing against that instead of needing to be re-pinned by hand whenever a slug dies.

**The doubled `openrouter/` is not a typo.** LiteLLM's own `openrouter/` custom-provider prefix gets stripped before the remainder is sent to OpenRouter's API — so to actually reach OpenRouter's `openrouter/free` model, the string handed to `litellm.completion(model=...)` has to be `openrouter/openrouter/free`. Passing just `openrouter/free` silently sends the single word `free` as the model id, which OpenRouter doesn't recognize (it comes back as a garbled error from a bogus "Stealth" provider, not a clean 404).

**Staying under the free-tier limit:**

- **Minimize calls per conversation.** Batch what can be batched — e.g. extract all fields the model can infer from a message in a single structured-output call, rather than one call per field.
- **Cache repeated requests.** If the same greeting or boilerplate prompt gets sent often (e.g. `GET /api/chat/greeting`), cache the response instead of hitting the model every time.
- **Debounce rapid user input.** Don't fire a model call on every keystroke or every partial message — wait for the user to finish typing/sending before calling out.
- **Retry once on failure, not in a loop.** A single retry against the same adaptive router can genuinely land on a different underlying free model if the first one it picked is down — but don't retry more than once per turn, and count each real attempt (see below) so a flaky first attempt doesn't silently double-spend quota unaccounted for.
- **Track usage locally.** Keep a simple in-memory or DB counter of requests made today, and warn (or queue) before hitting the 200/day ceiling — better than finding out via a failed request. Count every real attempt against the model, including retries, not just once per inbound user message.
- **Return clear errors on rate-limit hits**, rather than silently retrying in a loop, which can burn through remaining quota fast.

The `OPENROUTER_API_KEY` lives in the `.env` file at the project root.

## Technical architecture

The whole thing gets packaged into a Docker container.

- Backend: `backend/` directory, a uv project, FastAPI.
- Frontend: `frontend/` directory.
- Database: SQLite, rebuilt from scratch on every container start; includes a users table (signup and signin).
- The frontend is built as a static export (`output: "export"` in `next.config.ts`) and served directly by FastAPI, so the whole app is one process on one port.

Start/stop scripts in `scripts/`:

```bash
# Mac
scripts/start-mac.sh
scripts/stop-mac.sh

# Linux
scripts/start-linux.sh
scripts/stop-linux.sh

# Windows
scripts/start-windows.ps1
scripts/stop-windows.ps1
```

Backend available at: http://localhost:8010 (chosen over the more common 8000/3000 to avoid colliding with other local projects that default to those).

## Color palette

The base is blue and purple — neighbors on the color wheel (roughly 200°–260°), so they naturally work together. On top of that there's one warmer accent (amber, around 38°) in a triadic relationship to the base — it adds contrast on buttons/highlights without clashing, since it keeps a similar intensity. The heading color is just a darkened version of the blue, and the gray text has a slightly cool undertone so it doesn't stick out from the rest.

| Color            | Hex       | Usage               |
| ---------------- | --------- | ------------------- |
| Amber accent     | `#f2a541` | highlights, accents |
| Primary blue     | `#2e86ab` | —                   |
| Secondary purple | `#6a4c93` | submit buttons      |
| Dark navy        | `#1b2a4a` | headings            |
| Gray text        | `#7a7f87` | —                   |

## Implementation status

**Built (PREL-4 — V1 technical foundation):**

- Backend (`backend/`, FastAPI on uv): `POST /api/auth/signup`, `POST /api/auth/signin` (bcrypt + JWT bearer tokens), `GET /api/health`.
- SQLite `users` table, dropped and recreated on every app startup.
- Frontend built as a static export and served by FastAPI on one port.
- Single `Dockerfile` packaging backend + frontend together; start/stop scripts for mac/linux/windows in `scripts/` (app listens on **:8010** by default, not :8000, to avoid colliding with other local projects).

**Built (PREL-5 — AI chat, still just the Mutual NDA):**

- `GET /api/chat/greeting` (hardcoded, no LLM call) and `POST /api/chat/message` (stateless — frontend holds the message history) drive a freeform chat that fills in a document's fields. The manual form still exists as an editable fallback ("Step 2") in case the AI gets something wrong.
- Uses the adaptive `openrouter/openrouter/free` router described under "AI layer" above, with an in-memory daily-request counter enforcing the 200/day cap before every real attempt (including retries), and a hard-enforced request timeout (via a `ThreadPoolExecutor` + `future.result(timeout=...)`, not just litellm's own `timeout=` kwarg — that alone was verified live not to reliably bound the call for every model the adaptive router can pick).
- Chat is intentionally unauthenticated, matching the rest of the prototype — no login wall.

**Built (PREL-6 — all 11 document types):**

- `backend/app/templates.py` parses `catalog.json` + every `templates/*.md` file at startup into a generic structure (deduped fields, nested numbered body) — there's no more per-document hand-written content or components. `GET /api/documents` (catalog) and `GET /api/documents/{id}` (parsed template) serve this to the frontend, which renders it with generic `DocumentPreview`/`DocumentForm`/`DocumentPdfDocument` components (numbering is regenerated from nesting depth, not parsed from each template's literal markers).
- Chat now drives document-*type* selection too, not just field-filling: `document_id` is `null` until the assistant is confident which of the 11 the user needs. If the user asks for something unsupported, the system prompt instructs the model to say so and suggest the closest real match rather than setting `document_id`. The model's structured-output schema for `field_updates` is rebuilt per-request (`build_chat_reply_model`) from whichever document is currently active, so it's JSON-schema-constrained to that document's real field keys.
- Every document also gets 4 fixed party-name/address fields in addition to whatever its own body text references — most of these templates (including Mutual NDA) never name the two parties directly in their Standard Terms text, that's conventionally a separate Cover Page.

**Not yet built:**

- Document persistence (nothing is saved server-side beyond the current in-browser conversation).
- Frontend login/signup UI — the backend auth endpoints exist but nothing in `frontend/` calls them yet.
