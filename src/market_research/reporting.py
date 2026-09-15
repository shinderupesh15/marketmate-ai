"""Human-readable briefings assembled from checked fields, with approval-gated exports."""
import json
import re
from pathlib import Path
from market_research.schemas import CreatorBrief, Profile
from market_research.evidence import suitability

def text(value):
    # Escape HTML and Markdown metacharacters from untrusted product data.
    import html
    return re.sub(r"([\\\x60*_{}\[\]<>|])", r"\\\1", html.escape(str(value))).replace("\n", " ")

def claim_text(c):
    return f"{text(c.text)} [{c.source_id}]" if c else "Not verified"

def render_report(state):
    if "audience" in state.get("brief", {}):
        from market_research.market_reporting import render_market_report
        return render_market_report(state)
    brief = CreatorBrief.model_validate(state["brief"])
    lines = ["# CreatorKit AI", "", "**" + ("Approved" if state.get("approved") else "Draft — awaiting review") + "**",
             "", f"Created: {state.get('created_at', '')}", "",
             f"Goal: {text(brief.goal)}",
             f"Budget: {brief.currency} {brief.monthly_budget:g}/month · Device: {text(brief.device)} · Country: {text(brief.country)}",
             "", "## Recommendation", ""]
    rec = state.get("recommendation", {})
    lines += [text(rec.get("explanation", "Research is incomplete.")), ""]
    if rec.get("recommended_name"):
        lines += ["Recommended match: **" + text(rec["recommended_name"]) + "**", ""]
    for item in rec.get("tradeoffs", []):
        lines.append("- " + text(item))
    for raw in state.get("profiles", {}).values():
        p = Profile.model_validate(raw)
        fit = suitability(p, brief)
        lines += ["", "## " + text(p.name), "",
                  f"Fit: **{fit['status'].replace('_',' ')}**",
                  f"Plan: {text(p.price.plan)}",
                  f"Published price: {p.price.currency or ''} {p.price.amount if p.price.amount is not None else 'unknown'} / {p.price.interval}",
                  f"Listed price vs budget: {fit['published_price_status']}",
                  f"Total cost check: {text(fit['budget_note'])}",
                  f"Pricing evidence: {claim_text(p.price.evidence)}",
                  f"Positioning: {claim_text(p.positioning)}",
                  f"Device: {p.device.status} — {claim_text(p.device.evidence)}",
                  f"Region: {p.region.status} — {claim_text(p.region.evidence)}", "", "### Must-haves", ""]
        lines += [f"- {text(r.name)}: {r.verdict.status} — {claim_text(r.verdict.evidence)}" for r in p.requirements]
        lines += ["", "### Core features", ""] + ["- "+claim_text(c) for c in p.features]
        lines += ["", "### Restrictions and licensing", ""] + ["- "+claim_text(c) for c in p.restrictions]
        lines += ["", "### Recent news", ""]
        lines += [f"- {n.published_date}: {claim_text(n.evidence)}" for n in p.news] or ["No dated news verified in the selected window."]
        lines += ["", "### Gaps", ""] + ["- "+text(g) for g in p.gaps]
    lines += ["", "## Questions before choosing", ""]
    lines += ["- "+text(q) for q in rec.get("questions", [])]
    lines += ["", "## Research limitations", ""]
    lines += ["- "+text(e) for e in state.get("errors", [])]
    lines += ["- Prices and availability are research snapshots; verify before purchasing.",
              "- Exact quotation matching and a model review reduce unsupported claims but do not guarantee correctness.",
              "", "## Sources", ""]
    for s in state.get("sources", {}).values():
        safe_url = s["url"].replace(" ", "%20").replace("(", "%28").replace(")", "%29").replace(">", "%3E")
        lines.append(f"- [{s['id']}] [{text(s['title'])}]({safe_url}) — retrieved {s['retrieved_at']}; {s['content_level']}.")
    return "\n".join(lines)

def export_report(state, destination: Path):
    if not state.get("approved") or state.get("status") != "approved":
        raise PermissionError("Approve the current draft before export.")
    destination.mkdir(parents=True, exist_ok=True)
    for filename, content in (
        ("briefing.md", render_report(state)),
        ("briefing.json", json.dumps(state, indent=2, ensure_ascii=False)),
    ):
        temp = destination / (filename + ".tmp")
        temp.write_text(content, encoding="utf-8")
        temp.replace(destination / filename)
    return destination
