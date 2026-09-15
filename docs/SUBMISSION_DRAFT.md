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


## One-liner and success measure
MarketMate helps pre-launch founders research competing brands in a web app using You.com search/page retrieval and structured analysis, replacing manual browsing and comparison, then hands off a sourced briefing and proposed experiments for human review; the evaluation target is a usable briefing in under ten active minutes on eight of ten scoped cases.

That time/success rate is a future target, not an achieved benchmark. Three development cases completed after interventions. See MARKETMATE_VALIDATION.md for measured output coverage and disclosed repairs. No measured claim of hours saved is made.

## AI coding process and prompts
Codex was used to implement the Python graph, schemas, tool adapters, interface, and tests, and to investigate errors reported during manual testing. User instructions included:
- “Give another name and start implementing.”
- “Also, when I refresh the page, I can see a few texts which are gibberish.”
- “Review the code again, and we need to give the GitHub link also.”

Iterations included official-site resolution, evidence-preserving price handling, separating facts from experiments, filtering weak search results, bounded output retries, and explicit UTF-8 handling. The agent prompts themselves are in market_agents.py and models.py. BUILD_LOG.md records the main implementation decisions.

## Data and evaluation
Inputs are the user's business brief and public You.com web/news/page results. There is no training dataset or model fine-tuning. Synthetic fixtures exercise errors and human-review state without API calls. Live outputs are separate from fixture tests. Brand claims are attributed, not independently certified.

## Code link
https://github.com/shinderupesh15/marketmate-ai

Video link: add after recording. Google Doc link: create this document in Google Docs and enable reviewer access.
