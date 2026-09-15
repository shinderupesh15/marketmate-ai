# CreatorKit AI architecture

## Workflow

```mermaid
flowchart TD
    A[Creator brief] --> B[Discovery agent: search and identify vendors]
    B --> C{Three supported competitors?}
    C -->|No| D[Human clarification or partial scope]
    D --> B
    C -->|Yes| E[Research agent plans searches]
    E --> F[You.com web, page content, and news evidence]
    F --> G[Analysis agent produces typed profile]
    G --> H[Exact quotation checks and model verification]
    H --> I[Next product or orchestrator assessment]
    I -->|Material gap, within limits| E
    I -->|Ready or exhausted| J[Suitability checks and draft recommendation]
    J --> K[Human review]
    K -->|Targeted revision| E
    K -->|Approve| L[Markdown and JSON export]
```

All four roles share a configurable OpenAI model through LangChain. LangGraph controls routing and state.
The graph has bounded autonomy: agents select queries and the orchestrator decides whether another search is worth doing.
No multi-agent background processes or external orchestration accounts are required.

## Persistence and recovery

LangGraph uses a SQLite checkpointer and a stable run ID. Research input, selected competitors, evidence, profiles, current target, counters, errors, and approval are serialized as JSON-compatible state.
Provider keys live only in the configuration/client layer, never in checkpoints.

A separate events table journals request reservations before calls, so a process restart cannot reset a run's request allowance.
Query batches checkpoint at node boundaries. Work in a node interrupted by process termination may run again.
SQLite checkpoints do not imply exactly-once remote API calls.

Human interrupts handle ambiguous discovery, provider failures, and report approval.
Exports require both approved=true and status=approved and use atomic file replacement for repeatable saves.
A revision returns to research and leaves the report unapproved.

## Evidence rules

Every claim has a source ID and an exact supporting passage. Matching is case/whitespace normalized.
Invalid or missing references invalidate the field. A separate structured model call checks whether the field's meaning and plan applicability follow from the source.
Model verification is fallible and is described as a check, not a guarantee.

Published news dates must match source metadata and be within the configured window.
The registry retains retrieval dates and whether evidence came from an excerpt or extracted page content.
Prices retain billing cadence, source currency, tax status, and whether required additional costs are known.

Suitability applies hard rules in Python. It never treats unknown as a pass.
A paid base price under budget is still unknown if taxes or required extras cannot be established.
Annual amounts are divided by 12 only for comparison; users must explicitly allow upfront annual payment.
No foreign-exchange rate is invented.

## Deliberate first-version limits

Local single-user use, sequential competitor processing, no automatic purchase or external publication, no scheduled monitoring.
The interface does not generate videos or promise commercial rights to every included stock asset.
Historical snapshots and cross-run constraint-only recomputation are future enhancements.
