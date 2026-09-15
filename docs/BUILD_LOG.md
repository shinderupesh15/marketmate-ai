# Build log

## User direction and AI coding prompts

The user selected Week 3 Project 3A, the code-heavy market-research track, and OpenAI as model provider.
They then selected CreatorKit AI: a relatable assistant for creators choosing content tools.
The implementation request was: "Continue with the next step ... you can start implementing the plan."

This file summarizes the coding interaction; it is not a fabricated transcript of every prompt.
The handout's linked reference solutions were not opened or copied.

## Iterations

1. Built the Python/uv environment and secret-aware configuration loader. Five configuration tests passed.
2. Added typed creator briefs, source records, profiles, evidence-bearing claims, and recommendation contracts.
3. Added fixed-endpoint You.com HTTP calls with page extraction; a live probe returned four page-content sources.
4. Added structured LangChain calls for discovery, search planning, analysis, evidence verification, and orchestration.
5. Added SQLite checkpoints, persistent request counters, clarification/recovery/review interrupts, and approved export.
6. Built the native Streamlit form, comparisons, evidence viewer, saved-run navigation, and review/download controls.
7. Initial live discovery returned only two supported vendors and paused. Improved discovery to request official vendor URLs and use one broader follow-up before clarification.
8. Live discovery then selected CapCut, InShot, and VN Video Editor for comparison with Canva. Their suitability is determined by subsequent evidence, not assumed from popularity.
9. Added conservative rules for currency mismatch, tax uncertainty, annual billing, unsupported devices, and unknown must-haves.
10. Added atomic request reservations and handling for a partial report when request budgets are exhausted.

## Validation recorded during implementation

- Offline test suite: 27 passing tests, including ten suitability scenarios.
- Streamlit AppTest: brief submission through research, human approval, and downloads, using synthetic fixture agents.
- Recovery tests: service recreation preserves review state; transient failure resumes the same run; cancellation blocks export.
- Live API access: You.com search and OpenAI generation verified earlier; adapter extraction also verified.
- Local Streamlit server health endpoint returned ok.
- Real browser inspection could not run because browser automation hit the environment's sandbox setup error.

Ten suitability scenarios are NOT ten successful live end-to-end evaluations.
Live-run results and remaining unknowns must be recorded separately before claiming the proposed 8/10 success target.

11. Fixed unverified analysis notes leaking into the final summary. Recommendation prose is now assembled from checked fields; a regression test covers this.
12. Final structured model adapter and token logging passed a small live smoke test. See LIVE_RUN_REVIEW.md for the full demo outcome.
