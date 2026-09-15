# CreatorKit AI: agreed product scope

## Project statement

CreatorKit AI helps aspiring creators and small businesses choose affordable content-creation software, replacing manual searches, pricing comparisons, and feature checks. It discovers three alternatives to a shortlisted tool, investigates their capabilities, positioning, restrictions, and recent news, and produces a source-backed recommendation tailored to the user's device, goals, and budget, with human review before the shortlist is finalized.

Selected by the user: CreatorKit AI.
Proposed first demo persona: a home baker making Instagram reels on an Android phone in India with a monthly budget of INR 1,000.
The persona and defaults can be edited; they are not claims about any vendor's current pricing or availability.

## MVP boundary

Compare short-video creation/editing tools for a single creator. Start from a named tool and its official website so discovery remains faithful to Project 3A: research three competitors, not an arbitrary bundle of unrelated tools.
Use Canva as the proposed demo anchor, scoped to short-video creation rather than its entire product suite. Discover alternatives dynamically through You.com; never hardcode the three winners.
Briefly research the anchor too so comparisons with the user's starting option are evidence-based.

## Input form

- Content goal and intended audience (example: Instagram reels for a home bakery).
- Starting tool and official website.
- Country and currency (demo: India, INR).
- Device/platform (Android, iOS, desktop, or browser).
- Monthly budget and willingness to pay annually.
- Experience level and prioritized requirements.
- Must-haves: examples include watermark-free export, captions, vertical video, or own-media upload.
- News lookback (default 90 days).

## Output

1. Short recommendation explaining who the option suits and why.
2. Anchor plus three researched alternatives with sources.
3. Pricing with currency, billing cadence, annual commitment, included allowances, and taxes if documented.
4. Feature and suitability matrix: meets, does not meet, or unknown.
5. Device and regional availability with evidence.
6. Watermark/export restrictions, AI usage allowances, and documented commercial-use conditions.
7. Positioning/target audience and dated recent news for each competitor.
8. Limitations and questions the user should verify before purchase.
9. Reviewed Markdown briefing and structured JSON download.

No purchase, subscription signup, publishing, or cancellation is part of the MVP.
Tool subscriptions and music/stock-asset licenses are distinct: do not infer blanket commercial rights from a paid plan.
Do not describe the system as a video generator; it researches and recommends tools.

## Agent responsibilities

- Discovery: identify three relevant alternatives based on the same creator task, supported by public evidence.
- Research: collect official pricing, capabilities, supported platforms, restrictions, positioning, and dated announcements.
- Analysis: turn evidence into structured profiles and compare against the user's requirements.
- Orchestrator: coordinate the run, seek missing evidence, resolve ambiguous scope with the user, assemble the recommendation, and pause for final review.

Use the existing LangChain/LangGraph architecture, You.com primary search, OpenAI model connection, Streamlit interface, and SQLite persistence.

## Decision rules

Evaluate hard requirements before preferences. A confirmed failure on a must-have excludes a tool from the suitable shortlist; an unknown must-have means the tool needs verification.
Recommend a specific supported plan, not just a brand name. Do not claim a tool is within budget when price, currency, or mandatory costs are unknown.
Show annual-plan monthly equivalents separately from actual monthly billing. Do not invent exchange rates; retain source currency when reliable conversion is unavailable.
Avoid opaque numerical scores in the MVP. Explain the winning trade-offs and evidence instead.
If all options fail or remain uncertain, say so and ask whether to adjust constraints.
Keep three competitor profiles in the report even when some are unsuitable, so the user sees the alternatives considered.

## Demo walkthrough

Input: "I run a home bakery and want to make Instagram reels on Android. I am considering Canva. Compare three alternatives within INR 1,000 per month; watermark-free export is essential."

1. Show the editable user brief.
2. Discover three competitors and explain their relevance.
3. Display research progress and source collection.
4. Show the feature/pricing comparison and recommendation.
5. Change a constraint and recompute suitability, reusing still-current evidence when appropriate.
6. Demonstrate missing-information handling or a transient tool failure.
7. Review and approve the final report, then export.

## Implementation slices

1. Define creator brief, evidence, pricing, competitor profile, and recommendation schemas.
2. Implement the You.com adapter and one-tool evidence-to-profile workflow.
3. Implement discovery, three-competitor orchestration, and bounded follow-up.
4. Add suitability checks, durable state, failure recovery, and human review.
5. Build the Streamlit input/comparison/review interface.
6. Evaluate with real cases and deterministic failure fixtures, then prepare submission artifacts.

## Evaluation additions

Cover free-only budgets, monthly versus annual costs, unsupported devices, uncertain regional availability, missing pricing, unmet watermark requirements, and no suitable alternatives.
Measure sourced claim accuracy and whether a human can explain the recommendation from the evidence.
The existing target of a useful briefing within 10 minutes on 8/10 cases remains a proposed target, not an achieved result.
