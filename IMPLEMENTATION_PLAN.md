# Week 3: MarketMate AI implementation plan

Status: MarketMate implemented with competitor research, checked facts, proposed experiments, content ideas and human-reviewed export.

## 1. Page-by-page requirements

| Page | Contents and relevance |
| --- | --- |
| 1 | Build an agent that chooses next steps, calls tools, maintains state, recovers from errors, and hands off to humans. Lists August 30, 2026 for Builder of the Week and September 16, 2026 for final certification. |
| 2 | Project 3A: discovery agent finds top 3 competitors using You.com Search; research agent gathers fresh web/news evidence; analysis agent extracts pricing, features, positioning, and recent news; orchestrator delegates and compiles briefings. |
| 3 | Continuation of 3A: You.com is the primary search source; simple interface such as Streamlit; working formatted briefings and sample output for 2-3 competitors; demo and GitHub link or zip. Other use cases begin. |
| 4 | Project status and GTM use cases. Their persistent trend memory, document ingestion, and vector-store requirements do not apply to 3A. |
| 5 | Code review and IT support voice use cases; outside our scope. |
| 6 | Write a project one-liner. Measure task completion, explicitly design memory, and default business write actions to human approval. Detailed framework is optional. |
| 7 | Framework: goal, surface, ordered steps, tools, memory, limits, human review, error recovery, and success measure. |
| 8 | Code track: LangChain tools/agents, LangGraph state, checkpointers, interrupts, and LangSmith tracing/evals. Nebius wording is permissive ("may"), not a mandatory provider restriction. |
| 9 | Submit a Google Doc, video of 5 minutes or less, and code on GitHub. Document overview, datasets, AI coding prompts, iterations, and learnings. Demonstrate failure recovery and human review. |
| 10 | Links to reference solutions, with a warning against replication. Design this project independently; reference solutions were not opened. |

The page references in the introduction are inconsistent with the actual PDF: the framework is on pages 6-7, and Project 3A starts on page 2.
The general submission instructions request GitHub, although Project 3A also permits a zip; plan for GitHub to satisfy both.

## 2. Product and implementation

See [MarketMate scope](docs/MARKETMATE_SCOPE.md), [architecture](docs/ARCHITECTURE.md), and [live validation](docs/MARKETMATE_VALIDATION.md).

The app uses Python, LangChain, LangGraph, You.com and OpenAI. It preserves source evidence and supports bounded retries, follow-up research, durable history and approval before export.

## 3. Remaining submission work

Review the sample outputs, record the demo, publish the repository when ready, and submit the required links.
