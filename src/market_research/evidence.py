"""Validate citation passages and enforce conservative suitability rules."""
from datetime import date, timedelta
import re
from market_research.schemas import Profile, CreatorBrief, Verdict, Requirement

def clean(text):
    return re.sub(r"\s+", " ", text).strip().casefold()

def claim_fields(profile: Profile):
    fields = {}
    for key in ("positioning",):
        if getattr(profile, key):
            fields[key] = getattr(profile, key)
    if profile.price.evidence:
        for key in ("plan", "amount", "currency", "interval", "taxes", "mandatory_costs_known"):
            value = getattr(profile.price, key)
            if value is not None and value not in ("unknown", "Not verified") and value is not False:
                fields[f"price.{key}"] = profile.price.evidence
    for key in ("device", "region"):
        if getattr(profile, key).evidence:
            fields[key] = getattr(profile, key).evidence
    for key in ("features", "restrictions"):
        for i, claim in enumerate(getattr(profile, key)):
            fields[f"{key}.{i}"] = claim
    for i, req in enumerate(profile.requirements):
        if req.verdict.evidence:
            fields[f"requirements.{i}"] = req.verdict.evidence
    for i, item in enumerate(profile.news):
        fields[f"news.{i}"] = item.evidence
    return fields

def validate_passages(profile: Profile, sources: dict, brief: CreatorBrief, rejected=()):
    p = profile.model_copy(deep=True)
    # Accept nested paths returned by the reviewer as well as canonical claim paths.
    invalid = set()
    for path in rejected:
        if path.startswith(("device.", "region.")):
            path = path.split(".")[0]
        elif path.startswith(("requirements.", "features.", "restrictions.", "news.")):
            path = ".".join(path.split(".")[:2])
        invalid.add(path)
    for field, claim in claim_fields(p).items():
        src = sources.get(claim.source_id)
        if not src or len(clean(claim.quote)) < 12 or clean(claim.quote) not in clean(src["text"]):
            invalid.add("price" if field.startswith("price.") else field)
    if "price" in invalid or not p.price.evidence:
        p.price.plan = "Not verified"
        p.price.amount, p.price.currency, p.price.interval = None, None, "unknown"
        p.price.evidence = None
        p.price.mandatory_costs_known = False
        p.price.taxes = "unknown"
    else:
        resets = {"plan": "Not verified", "amount": None, "currency": None,
                  "interval": "unknown", "taxes": "unknown", "mandatory_costs_known": False}
        for key, replacement in resets.items():
            if f"price.{key}" in invalid:
                setattr(p.price, key, replacement)
        if any(k.startswith("price.") for k in invalid):
            p.price.evidence.text = "Supporting passage for retained pricing details; unresolved fields are shown separately."
            p.gaps.append("Some pricing details remain unverified; supported plan and billing details were retained.")
    if "positioning" in invalid:
        p.positioning = None
    for field in ("device", "region"):
        v = getattr(p, field)
        if field in invalid or not v.evidence:
            setattr(p, field, Verdict(status="unknown", evidence=None))
    for i, req in enumerate(p.requirements):
        if f"requirements.{i}" in invalid or not req.verdict.evidence:
            req.verdict = Verdict(status="unknown", evidence=None)
    for field in ("features", "restrictions"):
        setattr(p, field, [c for i, c in enumerate(getattr(p, field)) if f"{field}.{i}" not in invalid])
    news = []
    for i, item in enumerate(p.news):
        src = sources.get(item.evidence.source_id, {})
        try:
            published = date.fromisoformat(item.published_date)
            source_date = date.fromisoformat(str(src.get("published_at"))[:10])
            recent = date.today() - timedelta(days=brief.news_days) <= published <= date.today()
            if f"news.{i}" not in invalid and recent and published == source_date:
                news.append(item)
        except ValueError:
            pass
    p.news = news
    # Requirement names are controlled by user input, not invented by the model.
    by_name = {clean(r.name): r for r in p.requirements}
    p.requirements = [Requirement(name=n, verdict=by_name[clean(n)].verdict
                                  if clean(n) in by_name else Verdict(status="unknown", evidence=None))
                      for n in brief.must_haves]
    if invalid:
        p.gaps.append(f"{len(invalid)} unsupported field(s) removed during evidence checking.")
    if not p.news:
        p.gaps.append("No dated news verified within the selected lookback window.")
    p.gaps = list(dict.fromkeys(p.gaps))
    return p

def budget_check(profile: Profile, brief: CreatorBrief):
    p = profile.price
    if p.amount is None or p.amount < 0 or not p.evidence or p.interval == "unknown":
        return "unknown", None, "Price not verified."
    if p.interval == "free" and p.amount == 0:
        return ("meets" if p.mandatory_costs_known else "unknown"), 0, "Free plan; check documented restrictions."
    if p.currency != brief.currency:
        return "unknown", None, "Source currency differs; no exchange rate assumed."
    if p.interval == "year":
        if not brief.annual_ok:
            return "does_not_meet", p.amount / 12, "Requires an annual payment."
        monthly = p.amount / 12
    elif p.interval == "month":
        monthly = p.amount
    else:
        return "unknown", None, "One-time pricing is not a monthly subscription comparison."
    if monthly > brief.monthly_budget:
        return "does_not_meet", monthly, "Published price exceeds budget."
    if not p.mandatory_costs_known or p.taxes != "included":
        return "unknown", monthly, "Base price fits; taxes or mandatory costs need verification."
    return "meets", monthly, "Documented total fits the budget."

def published_price_check(profile: Profile, brief: CreatorBrief):
    p = profile.price
    if p.amount is None or p.amount < 0 or not p.evidence or p.interval == "unknown":
        return "unknown"
    if p.interval == "free":
        return "meets" if p.amount == 0 else "unknown"
    if p.currency != brief.currency:
        return "unknown"
    if p.interval == "year":
        if not brief.annual_ok:
            return "does_not_meet"
        amount = p.amount / 12
    elif p.interval == "month":
        amount = p.amount
    else:
        return "unknown"
    return "meets" if amount <= brief.monthly_budget else "does_not_meet"

def suitability(profile: Profile, brief: CreatorBrief):
    budget, monthly, note = budget_check(profile, brief)
    statuses = [budget, profile.device.status, profile.region.status] + [r.verdict.status for r in profile.requirements]
    status = "does_not_meet" if "does_not_meet" in statuses else ("unknown" if "unknown" in statuses else "meets")
    return {"status": status, "published_price_status": published_price_check(profile, brief), "budget_status": budget, "monthly_equivalent": monthly, "budget_note": note}
