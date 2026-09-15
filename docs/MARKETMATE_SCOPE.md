# MarketMate AI

MarketMate helps aspiring entrepreneurs and small businesses understand competing brands and plan affordable experiments.

## Inputs
Business idea, target audience, reference brand and official website, target market, and news lookback.

## Outputs
- The reference brand plus three discovered competitors.
- Sourced positioning, products/services, brand messaging, optional published price examples, and verified dated news.
- Up to three differentiation experiments with research basis, a practical test and an observable success signal.
- Up to five content concepts with a suggested format, outline and call to action.
- A proposed seven-day action plan and assumptions to validate.

Observed facts and proposed ideas are separate in the interface and report. A suggestion is not proof of demand, exclusivity or competitor weakness. A brand's marketing promise is attributed to the brand.

## Course alignment
Retains the Project 3A market-research workflow: discovery, research, analysis, orchestration, external search tools, durable state, bounded follow-up, and human review. Pricing and news are still researched but absent optional fields do not block synthesis.

## Implementation
The shared LangGraph accepts a brief type, profile type and empty-profile constructor from its agents. MarketMate runs use BusinessBrief, BusinessProfile and MarketPlan; CreatorKit schemas remain for earlier snapshots and regression tests.

MarketService stores new runs under data/marketmate. Original data/creatorkit.sqlite is preserved. The main Streamlit app and CLI now launch MarketMate.

Search retrieves official product pages, public positioning and news, and reads the brand homepage through You.com Contents. Discovery resolves missing official websites through a bounded additional search. Exact quotes, source existence, date checks and an independent model review filter factual claims. Synthesis references checked company/field pairs; unresolved references are dropped.

## Review and limits
Users can request two follow-up revisions, approve the briefing, or cancel. Only approved runs export Markdown and JSON. Thirty search/page requests, 36 model attempts, and a 600-second execution budget apply per run/invocation as documented in runtime.py.

No new service accounts or API keys. No publishing, purchasing, or customer outreach is automated.
