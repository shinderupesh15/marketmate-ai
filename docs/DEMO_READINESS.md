# Demo and submission readiness

## Verdict
Ready for a local, reviewed demonstration of Project 3A. Complete the video and Google Doc before submitting. This is a course demo, not a production deployment or a proven market-demand predictor.

## Handout review
All ten pages of the original handout were reread for this review.

| Requirement | Evidence / status |
| --- | --- |
| Three competing brands, primary You.com research (pp. 2–3) | Discovery identifies candidates and resolves official websites; user clarification if fewer than three |
| Specialist roles and orchestration (pp. 2–3) | MarketAgents discovery/research/analysis/synthesis roles routed by LangGraph; roles run sequentially rather than as separate background processes |
| Pricing, features, positioning, recent news (p. 2) | Typed products, positioning, messaging, price examples and dated news; unavailable evidence remains explicitly absent |
| Simple UI and formatted briefing (p. 3) | Streamlit; reviewed Markdown/JSON exports; repository includes an explicitly unapproved sample draft |
| State, memory and human review (pp. 6–8) | SQLite checkpoints across restarts; clarification, retry/partial/cancel, two revisions, approval before final export |
| Error handling (p. 9) | API retries, request limits, truncation handling, filtering error/unrelated pages; synthesis failure now has a direct retry |
| LangChain + LangGraph (p. 8) | LangChain structured model calls, LangGraph routing/checkpointer/interrupts; API adapters are Python methods, not a free-form ReAct agent |
| LangSmith tracing/evals (p. 8 building-block list) | Local event logs and pytest evaluations implemented. Hosted LangSmith traces are not configured; the handout lists it as a building block, not an explicit mandatory submission |
| Nebius (p. 8) | Optional wording (“may”); OpenAI is used |
| Google Doc (p. 9) | Content is prepared in SUBMISSION_DRAFT.md; user must create/share the Google Doc |
| Video <=5 minutes (p. 9) | Script below; recording still required |
| GitHub link (pp. 3, 9) | Public repository: https://github.com/shinderupesh15/marketmate-ai |
| Coding prompts, iterations, learnings (p. 9) | BUILD_LOG.md and SUBMISSION_DRAFT.md |

## Honest demo boundaries
- Demonstrate the tested food/drink cases. Other sectors are configurable but have not been live-validated.
- The saved examples do not contain verified recent news. Most prices are absent. Show these limitations rather than describing those fields as complete.
- Three prior development cases completed after fixes/resumes; this is not a 100% first-attempt success benchmark.
- A research session can exceed the five-minute recording window. Disclose saved results as previously generated live research.
- The app discovers relevant competitors; it does not prove market-share rankings or exhaustive local competition.
- Human review is still needed for brand claims and proposed business experiments.

## Five-minute recording outline
- 0:00–0:35: Problem, audience and one-liner.
- 0:35–1:10: Enter/edit a brief and show research starting.
- 1:10–2:00: Open a disclosed saved live run; inspect competitor facts and a source quotation.
- 2:00–3:00: Explain one differentiation experiment, content concept and first-week action.
- 3:00–4:00: Show source gaps, request a targeted revision, and explain retry/partial/cancel. Use a labeled fixture/recording for failure recovery if needed.
- 4:00–4:35: Personally review and approve the briefing; show downloads.
- 4:35–4:55: Show the repository, explain use of AI coding tools and remaining limitations.

## Submission checklist
1. Review a saved briefing and choose the demo case.
2. Record the <=5 minute video and set its sharing permissions.
3. Create/share the Google Doc using SUBMISSION_DRAFT.md.
4. Submit the video, Google Doc and GitHub links through the handout form.
