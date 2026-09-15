"""Render sourced observations and explicitly proposed business actions."""
from market_research.reporting import text, claim_text
from market_research.market_schemas import BusinessProfile
from market_research.market_agents import facts

def basis_claims(refs, profiles):
    result = []
    for ref in refs:
        raw = profiles.get(ref["company"])
        if raw:
            claim = facts(BusinessProfile.model_validate(raw)).get(ref["field"])
            if claim:
                result.append((ref["company"], claim))
    return result

def render_market_report(state):
    brief = state["brief"]
    lines = ["# MarketMate AI", "", "**Approved**" if state.get("approved") else "**Draft — awaiting review**",
             "", "Business idea: " + text(brief["goal"]), "Audience: " + text(brief["audience"]),
             "Market: " + text(brief["country"]), "Created: " + state.get("created_at", ""), ""]
    plan = state.get("recommendation", {})
    lines += [text(plan.get("explanation", "Research in progress.")), "", "## Competitor facts", ""]
    for raw in state.get("profiles", {}).values():
        p = BusinessProfile.model_validate(raw)
        lines += ["", "### " + text(p.name), "", "Positioning: " + claim_text(p.positioning)]
        for heading, claims in (("Products", p.products), ("Brand messaging",p.messaging), ("Published price examples",p.pricing)):
            lines += ["", "**"+heading+"**"] + ["- "+claim_text(c) for c in claims]
            if not claims:
                lines.append("No supported detail collected for this section.")
        lines += ["", "**Dated news**"] + [f"- {n.published_date}: {claim_text(n.evidence)}" for n in p.news]
        for gap in p.gaps:
            lines.append("- Research gap: " + text(gap))
    lines += ["", "## Ideas to test — proposals, not proven market gaps", ""]
    for item in plan.get("opportunities", []):
        lines += ["### "+text(item["title"]), text(item["proposal"]), "Test: "+text(item["test"]),
                  "Success signal: "+text(item["success_signal"])]
        for company, claim in basis_claims(item["basis"], state.get("profiles", {})):
            lines.append("Research basis — "+text(company)+": "+claim_text(claim))
    lines += ["", "## Content ideas — drafts to adapt and verify", ""]
    for item in plan.get("content_ideas", []):
        lines += ["### "+text(item["title"]), "Format: "+text(item["format"]), text(item["outline"]),
                  "Call to action: "+text(item["call_to_action"])]
        for company, claim in basis_claims(item["basis"], state.get("profiles", {})):
            lines.append("Research basis — "+text(company)+": "+claim_text(claim))
    lines += ["", "## Proposed first week", ""]
    lines += [f"- Day {a['day']}: {text(a['task'])} — Deliverable: {text(a['deliverable'])}" for a in plan.get("actions", [])]
    lines += ["", "## Assumptions to validate", ""] + ["- "+text(q) for q in plan.get("questions", [])]
    lines += ["", "## Limitations", "", "Public evidence is incomplete. Brand claims are not independently proven. Suggestions are hypotheses, not guaranteed outcomes."]
    lines += ["- "+text(e) for e in state.get("errors", [])]
    lines += ["", "## Sources", ""]
    for s in state.get("sources", {}).values():
        url = s["url"].replace(" ", "%20").replace("(", "%28").replace(")", "%29")
        lines.append(f"- [{s['id']}] [{text(s['title'])}]({url}) — retrieved {s['retrieved_at']}.")
    return "\n".join(lines)
