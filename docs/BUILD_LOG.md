# MarketMate implementation log

- Implemented business briefs, competitor facts, experiments, content ideas and first-week actions.
- Split candidate discovery from official-site resolution after live discovery returned a directory link.
- Bounded analysis excerpts after parallel live tests encountered OpenAI 429 errors; added a bounded transient-rate-limit retry.
- Restricted synthesis citations through a dynamic JSON schema of actual fact IDs after free-form field references caused valid-looking ideas to be dropped.
- Kept source-based observations separate from pre-launch proposals and labeled suggested success thresholds as targets to adjust.
- Existing API keys and dependency lock reused. No external posting, purchasing or remote Git push.

## Repository cleanup
- Removed the superseded toolkit implementation, documents, tests, saved data and diagnostics.
- Made MarketMate agents and service independent; retained shared transport, recovery, persistence and approval tests.
- Renamed the active database to marketmate.sqlite and verified its contents were unchanged. All three saved demo reports still render.
- Current suite: 23 passing tests. Local server restarted successfully.

## Paused-run and display fixes
- Fixed repeated Windows-1252/UTF-8 corruption in UI punctuation; UI separators now use plain text.
- Added explicit paused-step feedback and a retry button near the top of the saved run.
- Diagnosed repeated escaped nulls in model output from weak source input. Filtered error pages and unrelated-brand results before analysis.
- JSON-escape non-ASCII request data, request compact quotations, and retry truncated structured responses once with a bounded larger output limit and minimal-response instruction.
- Added sanitized model failure reasons and regression coverage for truncation, filtering and UI encoding.

## Demo readiness review
- Reread all ten handout pages and mapped Project 3A and code-track requirements to the implementation.
- Fixed synthesis failure recovery so the final plan can be retried without repeating research.
- Standardized code formatting/imports with Ruff; added UTF-8 editor settings and GitHub CI.
- Added a clearly unapproved sample briefing, readiness checklist, and recording outline.
- Local validation: 29 tests passed, lint/format passed, and installed dependencies passed compatibility checks.
- Checked 80 Git-history blobs plus publication files for configured credentials and OpenAI key patterns; found no matches.
