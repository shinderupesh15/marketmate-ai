# MarketMate AI: submission draft

## Problem and result
Small-business founders spend time researching competitors but struggle to turn that research into a practical launch plan. MarketMate researches a reference brand and three competitors, then proposes differentiation experiments, content ideas and a first-week action plan.

## Agent workflow
1. Discovery identifies comparable brands and resolves their official websites.
2. Research collects product, positioning, price and dated news evidence.
3. Analysis checks exact quotations and semantic support.
4. Orchestration follows up on missing core evidence and synthesizes proposals from checked facts.
5. The user reviews, requests revisions, and approves export.

## Stack
Python, LangChain, LangGraph, OpenAI, You.com Search/Contents, Pydantic, SQLite and Streamlit. Existing project keys and dependency lock are reused.

## Evidence versus suggestions
Facts have source IDs and supporting quotations. Brand messaging is attributed. Business ideas are labeled hypotheses and include tests; the system does not establish market demand or guarantee results. Missing optional pricing does not prevent useful product research.

## Suggested demo
- Enter a business idea, audience, market and a reference brand.
- Show dynamically discovered competitors and one sourced product fact.
- Inspect an experiment and its research basis.
- Show five content ideas and proposed first-week deliverables.
- Request a follow-up, then approve and export.
- If using a saved run, disclose it as previously generated live research.

## Submission actions
Review measured live evaluations, record the demo, create/share the GitHub repository and submission document, and provide the required links. Local implementation is not a completed course submission.
