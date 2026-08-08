# Prelegal — project documentation

## What it is

Prelegal is a SaaS app where users generate legal agreements from ready-made templates stored in the `templates` directory. The field-filling process happens through a conversation with an AI assistant — it's the assistant that figures out which document is needed and what data should go into it.

The full list of supported documents lives in `catalog.json` at the repo root:

@catalog.json

The system currently supports all 11 document types, along with full user authentication and document persistence.

## How feature work happens

1. Pull the feature requirements from Jira (Atlassian tools).
2. Implement the feature, following all 7 steps of the feature-dev process — none get skipped.
3. Write unit and integration tests, verify behavior thoroughly, and fix any bugs found.
4. Open a PR via the GitHub tools.

## AI layer

For talking to language models, use LiteLLM through OpenRouter, calling the free variant of the model directly: `openai/gpt-oss-120b:free`. No separate inference provider needs to be configured — OpenRouter serves this model at no cost (rate-limited to 20 requests/min and 200 requests/day, no credit card required). Responses should use Structured Outputs so they can be parsed easily and used to populate document fields.

**Staying under the free-tier limit:**

- **Minimize calls per conversation.** Batch what can be batched — e.g. extract all fields the model can infer from a message in a single structured-output call, rather than one call per field.
- **Cache repeated requests.** If the same greeting or boilerplate prompt gets sent often (e.g. `GET /api/chat/greeting`), cache the response instead of hitting the model every time.
- **Debounce rapid user input.** Don't fire a model call on every keystroke or every partial message — wait for the user to finish typing/sending before calling out.
- **Add a fallback model.** Free `:free` model availability on OpenRouter rotates often — providers pull or reprice free endpoints without notice — so don't hard-wire a second fixed model ID as the fallback. Instead, configure LiteLLM to fall back to `openrouter/free`, OpenRouter's own auto-router, which picks whichever free model is currently available while filtering for the capabilities the request needs (e.g. structured output/tool calling). If `openai/gpt-oss-120b:free` hits its limit, the fallback call goes to `openrouter/free` instead of failing outright. Periodically check openrouter.ai/models for what's currently free, in case a more suitable fixed model is worth pinning later.
- **Track usage locally.** Keep a simple in-memory or DB counter of requests made today, and warn (or queue) before hitting the 200/day ceiling — better than finding out via a failed request.
- **Return clear errors on rate-limit hits**, rather than silently retrying in a loop, which can burn through remaining quota fast.

The `OPENROUTER_API_KEY` lives in the `.env` file at the project root.

## Technical architecture

The whole thing gets packaged into a Docker container.

- Backend: `backend/` directory, a uv project, FastAPI.
- Frontend: `frontend/` directory.
- Database: SQLite, rebuilt from scratch on every container start; includes a users table (signup and signin).
- Worth considering: building the frontend as a static export and serving it directly through FastAPI, if feasible.

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

Backend available at: http://localhost:8000

## Color palette

The base is blue and purple — neighbors on the color wheel (roughly 200°–260°), so they naturally work together. On top of that there's one warmer accent (amber, around 38°) in a triadic relationship to the base — it adds contrast on buttons/highlights without clashing, since it keeps a similar intensity. The heading color is just a darkened version of the blue, and the gray text has a slightly cool undertone so it doesn't stick out from the rest.

| Color            | Hex       | Usage               |
| ---------------- | --------- | ------------------- |
| Amber accent     | `#f2a541` | highlights, accents |
| Primary blue     | `#2e86ab` | —                   |
| Secondary purple | `#6a4c93` | submit buttons      |
| Dark navy        | `#1b2a4a` | headings            |
| Gray text        | `#7a7f87` | —                   |
