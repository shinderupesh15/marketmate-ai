# MarketMate live validation

Three development cases reached human review using live You.com and OpenAI requests. No report was automatically approved.

| Case | Run ID | Brand profiles | Supported claims | Sources | Experiments | Content ideas | Action steps |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Healthy snacks / The Whole Truth | 5d1f47650769428f9bb5628cb9e857f6 | 4 | 21 | 85 | 3 | 5 | 7 |
| Home coffee / Blue Tokai | 51c8e4b72c274eb2ba6711ff4f80e40e | 4 | 8 | 83 | 3 | 5 | 7 |
| Regional fruit drinks / Paper Boat | acbc8ce72ac24514999013dccbead30a | 4 | 22 | 95 | 3 | 5 | 7 |

All retained factual passages were checked again against the saved source registry. Idea references resolve to existing checked company fields. Claims also passed a model evidence review, which is fallible; these counts are not independent human accuracy scores.

The healthy-snack draft rendered in Streamlit AppTest with no exceptions. Its five tabs and human-review controls appeared. The local Streamlit health endpoint returned OK.

## Development interventions
These are completed development examples, not three untouched first-attempt successes or a measured reliability benchmark.
- Discovery was refined to resolve official websites separately; the coffee case was resumed with a clarification.
- Parallel runs hit OpenAI 429 errors. Saved runs were resumed, source context was reduced, and transient rate-limit retry support was added.
- Draft synthesis was rerun after restricting references to allowed fact IDs and clarifying pre-launch instructions.
- The first earlier snack discovery attempt remains a partial saved run. Use the IDs above for the completed drafts.

## Remaining limits
Coffee coverage was thinner (8 supported claims). Some positioning, pricing and dated-news sections remain absent; product evidence can still support proposed experiments. Sources can be stale, promotional or incomplete. Proposed thresholds are adjustable targets, not research benchmarks. There is no evidence yet that users will buy the proposed products.

## Demo
Open a saved research case in the sidebar, inspect a competitor fact and its quotation, then open Ideas to test, Content studio and First-week plan. Disclose saved runs as previously generated live research. Approve only after personally reviewing the draft.
