"""Keep primary pricing evidence in context as research accumulates."""
from urllib.parse import urlparse

def official_source(url, company_url):
    host = (urlparse(url).hostname or "").removeprefix("www.").lower()
    vendor = (urlparse(company_url).hostname or "").removeprefix("www.").lower()
    return host == vendor or host.endswith("." + vendor)

def pricing_source(source):
    return any(term in source["url"].lower() for term in ("pricing", "price", "subscription", "payment", "billing", "/plans"))

def select_sources(ids, sources, company_url, limit=12):
    ordered = list(dict.fromkeys(sid for sid in ids if sid in sources))
    # Prefer newest copy of a URL; otherwise identical pages crowd out different evidence.
    latest = {}
    for sid in ordered:
        src = sources[sid]
        previous = latest.get(src["url"])
        if previous is None or (src["retrieved_at"], len(src["text"])) >= (sources[previous]["retrieved_at"],len(sources[previous]["text"])):
            latest[src["url"]] = sid
    ordered = list(latest.values())
    primary_prices = [sid for sid in ordered if official_source(sources[sid]["url"],company_url) and pricing_source(sources[sid])]
    primary_prices.sort(key=lambda sid:(len(sources[sid]["text"]) > 400, sources[sid]["retrieved_at"]),reverse=True)
    picked = primary_prices[:4]
    # Preserve room for news, then other current device/feature evidence.
    news = [sid for sid in reversed(ordered) if sources[sid].get("kind") == "news"]
    picked += [sid for sid in news[:2] if sid not in picked]
    ranked = sorted(ordered, key=lambda sid:(official_source(sources[sid]["url"],company_url), sources[sid]["retrieved_at"]), reverse=True)
    picked += [sid for sid in ranked if sid not in picked]
    return {sid:sources[sid] for sid in picked[:limit]}
