# CreatorKit AI

A local research assistant that helps creators choose short-video tools for their goals, device, and budget.
Built for Week 3 Project 3A with Python, LangChain, LangGraph, You.com Search, and OpenAI.

## What it does

- Researches a starting tool and discovers three competitors dynamically.
- Gathers public pricing, capabilities, positioning, restrictions, and dated news.
- Checks exact evidence passages and runs a separate model verification pass.
- Applies budget, device, region, and must-have constraints conservatively.
- Saves progress in SQLite and pauses for clarification, recovery, and final review.
- Exports approved Markdown and JSON briefings.

The default editable example is a home baker considering Canva for Instagram reels on Android in India, with an INR 1,000 monthly budget.

## Setup (PowerShell)

Python 3.13 and uv are used locally. The exact dependency resolution is in uv.lock.

```powershell
uv sync --locked
```

For a fresh clone only, copy .env.example to .env. Do not overwrite existing credentials.

```dotenv
YDC_API_KEY=
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1-mini
```

Settings load from the project-root .env. Environment variables take precedence.
Keys are masked by the settings model and never included in saved research state.
Never print get_secret_value() or save real keys in notebooks.

## Run

```powershell
uv run --locked streamlit run streamlit_app.py --server.address 127.0.0.1
```

Open http://127.0.0.1:8501. Fill the brief, start research, and review the evidence before approving.
Use the sidebar to reopen a saved run. After a restart, use Resume saved research.
If a run is paused for an API error, fix the local configuration or provider quota and choose Retry failed step.
Completed research is kept; the interrupted node may repeat its unfinished work.

For a terminal-based live research run (uses API credits and pauses for review):

```powershell
uv run --locked python -m market_research.cli
```

Review this run in the web app. The CLI does not automatically approve reports.

## Checks

```powershell
uv run --locked python -m market_research.check_setup
uv run --locked pytest -q
uv pip check
```

Tests use fake credentials, mock HTTP responses, and synthetic evidence; they do not incur API charges.
The offline setup check verifies configuration, imports, and a LangGraph/SQLite checkpoint round-trip.

## Scope and limits

- Short-video tool comparison for one creator, one country/device, and up to six must-haves.
- Three competitors plus the starting tool. Missing/ambiguous discovery pauses for clarification.
- At most 30 search requests and 36 model requests per run, including retries. At most two autonomous follow-up searches and two user revision rounds.
- A 10-minute active-execution budget per invocation, excluding human waiting. Persistent request counters apply across retries and restarts.
- API requests cost money. Request limits bound usage but are not an exact currency spending cap.
- A source record keeps up to 16,000 characters; an analysis pass uses up to 12 recent source records for that product.
- Tax uncertainty, currency mismatch, and missing region/device evidence produce unknown suitability rather than an invented match.
- News requires a source metadata date inside the chosen window. Missing metadata can exclude otherwise relevant announcements.
- Evidence matching and a second model pass reduce errors; they do not guarantee factual accuracy.
- No purchasing, signup, publishing, or cancellation. No automatic final approval.
- Local single-user app; bind to localhost. Authentication and multi-user deployment are not implemented.

## Local data

data/creatorkit.sqlite stores checkpoints, source passages, run history, and sanitized event logs.
data/exports/<run-id>/ holds approved exports. These files are ignored by Git.
Run data remains locally until explicitly removed. Do not delete the database while the app is running.
Fresh runs fetch new evidence; old reports retain their original retrieval dates.

## IDE and Jupyter

Select .venv/Scripts/python.exe as the Python interpreter and notebook kernel.
ipykernel is installed; a global kernel registration is unnecessary.

## Repository guide

- streamlit_app.py: input, comparison, evidence, history, review, and download UI.
- src/market_research/schemas.py: creator brief and research contracts.
- tools.py: bounded You.com search with extraction.
- models.py and agents.py: structured model calls and specialist roles.
- evidence.py: citation matching and deterministic suitability rules.
- graph.py: research routing, bounded follow-up, interrupts, and recovery.
- service.py and runtime.py: SQLite lifecycle, history, and usage limits.
- reporting.py: Markdown rendering and approval-gated exports.
- tests/: offline evidence, failure, persistence, budget, and UI tests.
- docs/CREATORKIT_SCOPE.md: agreed product scope.
- docs/ARCHITECTURE.md: technical design.
- docs/SUBMISSION_DRAFT.md: documentation outline and demo script.
- docs/BUILD_LOG.md: implementation decisions and validation notes.
