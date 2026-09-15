"""Durable research orchestration with explicit human review and recovery."""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from market_research.market_schemas import BusinessBrief, BusinessProfile, empty_profile
from market_research.retrieval import select_sources
from market_research.runtime import BudgetExceeded, ServiceError


class State(TypedDict, total=False):
    brief: dict
    created_at: str
    competitors: list
    sources: dict
    profiles: dict
    company_sources: dict
    queue: list
    target: dict
    queries: list
    errors: list
    followups: int
    revision_count: int
    recommendation: dict
    approved: bool
    status: str
    next: str
    feedback: str
    clarification: str
    failed_node: str
    event: str


def build_graph(agents, saver):
    def wrap(name, fn):
        def run(state):
            agents.usage.record("stage", name)
            try:
                result = fn(state)
                result["event"] = name.replace("_", " ").title()
                return result
            except BudgetExceeded as exc:
                return {
                    "status": "partial",
                    "next": "compile",
                    "approved": False,
                    "errors": state.get("errors", []) + [str(exc)],
                    "event": "Budget reached",
                }
            except ServiceError as exc:
                return {
                    "status": "needs_help",
                    "next": "recovery",
                    "failed_node": name,
                    "errors": state.get("errors", []) + [str(exc)],
                    "event": "Research paused",
                }

        return run

    def discovery(state):
        brief = BusinessBrief.model_validate(state["brief"])
        competitors, sources, clarification = agents.discover(brief, state.get("feedback", ""))
        combined = {**state.get("sources", {}), **sources}
        anchor = {
            "name": brief.anchor_name,
            "url": brief.anchor_url,
            "reason": "Your starting option",
            "source_ids": [],
        }
        next_node = "clarify" if clarification or len(competitors) != 3 else "choose_target"
        return {
            "competitors": competitors,
            "sources": combined,
            "queue": [anchor, *competitors],
            "clarification": clarification or "Fewer than three supported competitors found.",
            "next": next_node,
            "status": "researching",
        }

    def clarify(state):
        answer = interrupt(
            {
                "type": "clarification",
                "message": state["clarification"],
                "options": ["clarify", "partial", "cancel"],
            }
        )
        if answer.get("action") == "cancel":
            return {"status": "cancelled", "next": "end", "approved": False}
        if answer.get("action") == "partial":
            return {
                "next": "choose_target",
                "errors": state.get("errors", [])
                + ["User continued with an incomplete/ambiguous competitor set."],
            }
        return {"feedback": str(answer.get("feedback", ""))[:1000], "next": "discovery"}

    def choose_target(state):
        queue = state.get("queue", [])
        if not queue:
            return {"next": "orchestrate"}
        return {"target": queue[0], "queue": queue[1:], "queries": [], "next": "research"}

    def research(state):
        brief = BusinessBrief.model_validate(state["brief"])
        company = state["target"]
        queries = state.get("queries") or agents.plan_research(brief, company)
        sources = dict(state.get("sources", {}))
        mapping = dict(state.get("company_sources", {}))
        ids = list(mapping.get(company["name"], []))
        errors = list(state.get("errors", []))
        exhausted = False
        for q in queries[:3]:
            try:
                found = agents.search.search(
                    q["query"],
                    q["kind"],
                    brief.news_days,
                    **({"domains": q["domains"]} if q.get("domains") else {}),
                )
                for source in found:
                    sources[source.id] = source.model_dump()
                    ids.append(source.id)
                if not found:
                    errors.append(f"{company['name']}: search returned no usable evidence.")
            except ServiceError as exc:
                errors.append(f"{company['name']}: {exc}")
                if isinstance(exc, BudgetExceeded):
                    exhausted = True
                    break
        # Fetch the official brand homepage once during initial research.
        if not exhausted and not state.get("queries") and hasattr(agents.search, "read_pages"):
            urls = [company["url"]]
            if urls:
                try:
                    for source in agents.search.read_pages(urls):
                        sources[source.id] = source.model_dump()
                        ids.append(source.id)
                except ServiceError as exc:
                    errors.append(
                        f"{company['name']}: direct page extraction unavailable; using search evidence. {exc}"
                    )
                    exhausted = isinstance(exc, BudgetExceeded)
        mapping[company["name"]] = list(dict.fromkeys(ids))
        if exhausted:
            return {
                "sources": sources,
                "company_sources": mapping,
                "errors": errors,
                "next": "compile",
                "status": "partial",
                "approved": False,
            }
        if not ids:
            return {
                "sources": sources,
                "company_sources": mapping,
                "errors": errors,
                "next": "recovery",
                "failed_node": "research",
                "status": "needs_help",
            }
        return {
            "sources": sources,
            "company_sources": mapping,
            "errors": errors,
            "next": "analyze",
            "status": "researching",
        }

    def analyze(state):
        brief = BusinessBrief.model_validate(state["brief"])
        target = state["target"]
        ids = state.get("company_sources", {}).get(target["name"], [])
        # Bound model context; retain the full source registry in the saved report.
        sources = select_sources(ids, state["sources"], target["url"])
        profile = agents.analyze(brief, target, sources)
        profiles = {**state.get("profiles", {}), target["name"]: profile.model_dump()}
        return {"profiles": profiles, "queries": [], "next": "choose_target", "approved": False}

    def orchestrate(state):
        if state.get("followups", 0) >= 2 or state.get("status") == "partial":
            return {"next": "compile"}
        brief = BusinessBrief.model_validate(state["brief"])
        decision = agents.followup(brief, state.get("profiles", {}))
        candidates = [
            {"name": brief.anchor_name, "url": brief.anchor_url},
            *state.get("competitors", []),
        ]
        target = next((c for c in candidates if c["name"] == decision.target_name), None)
        agents.usage.record("decision", decision.reason)
        if decision.action == "research" and target and decision.query:
            return {
                "target": target,
                "queries": [{"query": decision.query, "kind": "web"}],
                "followups": state.get("followups", 0) + 1,
                "next": "research",
            }
        return {"next": "compile"}

    def compile_report(state):
        brief = BusinessBrief.model_validate(state["brief"])
        profiles = dict(state.get("profiles", {}))
        companies = [
            {"name": brief.anchor_name, "url": brief.anchor_url},
            *state.get("competitors", []),
        ]
        for c in companies:
            if c["name"] not in profiles:
                profiles[c["name"]] = empty_profile(
                    c["name"], c["url"], brief, "Research incomplete."
                ).model_dump()
        try:
            recommendation = agents.recommend(
                brief, [BusinessProfile.model_validate(p) for p in profiles.values()]
            ).model_dump()
        except BudgetExceeded as exc:
            recommendation = {
                "opportunities": [],
                "content_ideas": [],
                "actions": [],
                "explanation": "No final recommendation is available. Review the collected evidence and unresolved fields.",
                "questions": [str(exc)],
            }
        except ServiceError as exc:
            return {
                "profiles": profiles,
                "approved": False,
                "status": "needs_help",
                "next": "recovery",
                "failed_node": "compile",
                "errors": state.get("errors", []) + [str(exc)],
            }
        return {
            "profiles": profiles,
            "recommendation": recommendation,
            "approved": False,
            "status": "review",
            "next": "review",
        }

    def review(state):
        answer = interrupt(
            {
                "type": "review",
                "message": "Review the evidence and limitations before finalizing.",
                "options": ["approve", "revise", "cancel"],
            }
        )
        if answer.get("action") == "approve":
            return {"approved": True, "status": "approved", "next": "end"}
        if answer.get("action") == "cancel":
            return {"approved": False, "status": "cancelled", "next": "end"}
        target_name = answer.get("target_name")
        profiles = state.get("profiles", {})
        query = str(answer.get("feedback", "")).strip()[:700]
        if target_name not in profiles or not query:
            return {"next": "review", "approved": False}
        if state.get("revision_count", 0) >= 2:
            return {
                "next": "review",
                "errors": state.get("errors", [])
                + ["Revision limit reached; start a new brief for more research."],
                "approved": False,
            }
        target = profiles[target_name]
        return {
            "target": {"name": target["name"], "url": target["url"]},
            "queries": [{"query": target_name + " " + query, "kind": "web"}],
            "next": "research",
            "status": "researching",
            "approved": False,
            "revision_count": state.get("revision_count", 0) + 1,
        }

    def recovery(state):
        answer = interrupt(
            {
                "type": "recovery",
                "message": state.get("errors", ["Research needs attention."])[-1],
                "options": ["retry", "partial", "cancel"],
            }
        )
        action = answer.get("action")
        if action == "cancel":
            return {"next": "end", "status": "cancelled", "approved": False}
        if action == "partial":
            return {"next": "compile", "status": "partial", "approved": False}
        return {"next": state["failed_node"], "status": "researching"}

    graph = StateGraph(State)
    nodes = {
        "discovery": wrap("discovery", discovery),
        "clarify": clarify,
        "choose_target": choose_target,
        "research": wrap("research", research),
        "analyze": wrap("analyze", analyze),
        "orchestrate": wrap("orchestrate", orchestrate),
        "compile": compile_report,
        "review": review,
        "recovery": recovery,
    }
    for name, fn in nodes.items():
        graph.add_node(name, fn)
    graph.add_edge(START, "discovery")
    destinations = {n: n for n in nodes} | {"end": END}
    for name in nodes:
        graph.add_conditional_edges(name, lambda state: state["next"], destinations)
    return graph.compile(checkpointer=saver)
