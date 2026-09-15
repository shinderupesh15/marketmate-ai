# CreatorKit AI: submission documentation draft

## Overview

CreatorKit AI helps aspiring creators and small businesses compare content-creation tools for their goals, device, and budget.
It researches a starting tool and three competitors, validates supporting passages, compares suitability, and asks for human review before export.

## Demo persona

A home baker in India wants to make Instagram reels on Android, is considering Canva, and has an INR 1,000 monthly budget.
Watermark-free export is a must-have. The inputs are editable and the competitors are discovered dynamically.

## Data sources

Live You.com web/news search and extracted public pages. Prefer official pricing, product documentation, device support, and dated announcements.
Every source is stored with URL, retrieval timestamp, supporting text, and publication metadata where available.
Tests use explicitly synthetic profiles and mock HTTP responses; no training dataset is used.

## Implementation

Python, LangChain, LangGraph, OpenAI, You.com, Pydantic, SQLite, and Streamlit.
See ARCHITECTURE.md for graph and state behavior, and BUILD_LOG.md for coding prompts, iterations, and verification.
The implementation uses structured outputs and tool adapters; it does not train or fine-tune a model.

## Learnings

- Discovery should separate product identity from app-store domains.
- Low prices are not enough: billing cadence, taxes, platform availability, and plan restrictions affect suitability.
- An exact source quote alone does not prove a claim; semantic support also needs checking.
- Explicit unknowns and useful partial results are necessary for a credible research workflow.
- Approval must be preserved in graph state, not only a UI checkbox.

## Suggested demo script (under five minutes)

- 0:00-0:35: Explain the home-bakery problem and creator brief.
- 0:35-1:10: Start a live research run and explain discovery, research, analysis, and orchestration.
- 1:10-2:15: Show a saved completed draft while live research progresses; clearly disclose this is a previously recorded run.
- 2:15-3:10: Inspect pricing, must-haves, evidence passages, and uncertain findings.
- 3:10-3:50: Show a recovery fixture or recorded recovery example, clearly labeled as simulated, and explain saved-state resume.
- 3:50-4:35: Review a real draft, approve it yourself, and download the briefing.
- 4:35-4:55: Explain use of AI coding tools, tests, and limitations.

Do not promise a live multi-minute research run will finish inside the five-minute recording.
The final video should still show the actual running app and actual output, with saved/fixture material labeled.

## Remaining submission actions

- Human review of the live sample, including pricing and regional availability.
- Record measured end-to-end evaluations; do not present the success target as an achieved result.
- Paste finalized documentation into a Google Doc.
- Record the demo and create/share the GitHub repository.
- Submit the actual links through the handout form.
