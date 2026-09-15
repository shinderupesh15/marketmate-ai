# Pricing evidence improvements

- Search the official vendor domain for plans before broad feature/news queries.
- Fetch up to two discovered official pricing URLs through You.com Contents; count these against the existing 30-request budget.
- Keep official pricing evidence in the 12-source analysis context as later evidence arrives.
- Retain independently supported plan, amount, currency and billing fields when tax or extra-cost evidence is absent.
- Separate factual extraction review from budget suitability. Preserve source currencies; do not infer local prices from localized URLs.
- Display published-price budget fit separately from total-cost fit, with the pricing passage and source link.
- Accept nested reviewer rejection paths so unsupported verdicts are removed.

## Live validation
The old Canva India pricing search result contained 295 characters. A direct Contents read recovered 16,000 characters, including USD annual prices. The revised analysis retained Pro at USD 144/year; that is the provider-returned snapshot, not a verified Indian checkout price. Device, region and plan-specific export claims still require separate evidence.

Saved research remains a snapshot. Start a new brief to use the improved full retrieval flow. Existing reports were not overwritten.

## Remaining limitations
JavaScript, geolocation, app-store billing and checkout-only taxes may remain inaccessible. No conversion or inferred local price is substituted. A different demo scope is optional; another API key is not needed for this improvement.
