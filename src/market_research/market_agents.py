"""Market specialists with checked facts and explicitly speculative synthesis."""
import re
from datetime import date, timedelta
from typing import Literal
from pydantic import create_model, Field
from urllib.parse import urlparse
from market_research.agents import Agents
from market_research.schemas import Discovery, EvidenceReview, FollowUp, Candidate
from market_research.market_schemas import BusinessBrief, BusinessProfile, MarketPlan, Experiment, ContentIdea, empty_profile
from market_research.evidence import clean
from market_research.retrieval import official_source

def facts(profile):
    result = {}
    if profile.positioning:
        result["positioning"] = profile.positioning
    for field in ("products", "messaging", "pricing"):
        result.update({f"{field}.{i}": c for i, c in enumerate(getattr(profile, field))})
    for i, item in enumerate(profile.news):
        result[f"news.{i}"] = item.evidence
    return result

def validate_profile(profile, sources, brief, rejected=()):
    p = profile.model_copy(deep=True)
    invalid = set()
    for path in rejected:
        invalid.add(".".join(path.split(".")[:2]) if "." in path and path.split(".")[1].isdigit() else path.split(".")[0])
    for path, claim in facts(p).items():
        source = sources.get(claim.source_id)
        if not source or len(clean(claim.quote)) < 12 or clean(claim.quote) not in clean(source["text"]):
            invalid.add(path)
    if "positioning" in invalid:
        p.positioning = None
    for field in ("products", "messaging", "pricing"):
        setattr(p, field, [c for i,c in enumerate(getattr(p, field)) if field not in invalid and f"{field}.{i}" not in invalid])
    news = []
    for i, item in enumerate(p.news):
        source = sources.get(item.evidence.source_id, {})
        try:
            published = date.fromisoformat(item.published_date)
            if ("news" not in invalid and f"news.{i}" not in invalid
                    and str(source.get("published_at", ""))[:10] == str(published)
                    and date.today()-timedelta(days=brief.news_days) <= published <= date.today()):
                news.append(item)
        except ValueError:
            pass
    p.news = news
    if invalid:
        p.gaps.append(f"{len(invalid)} unsupported claim(s) removed during review.")
    return p

def checked_plan(plan, profiles):
    allowed = {(p.name, field) for p in profiles for field in facts(p)}
    p = plan.model_copy(deep=True)
    for field in ("opportunities", "content_ideas"):
        setattr(p, field, [idea for idea in getattr(p, field)
            if idea.basis and all((r.company, r.field) in allowed for r in idea.basis)])
        for idea in getattr(p, field):
            for name in type(idea).model_fields:
                value = getattr(idea, name)
                if isinstance(value, str):
                    setattr(idea, name, re.sub(r"\s*\(F\d+(?:,\s*F\d+)*\)", "", value))
    for idea in p.opportunities:
        idea.success_signal = "Proposed target to adjust: " + idea.success_signal
    count = sum(len(facts(profile)) for profile in profiles)
    p.explanation = f"Research collected {count} supported claims across {len(profiles)} brands. These ideas are proposals to test, not proven market gaps or demand."
    if not p.opportunities or not p.content_ideas:
        p.questions.append("Evidence was insufficient for some ideas; refine the scope or request more research.")
    return p

class MarketAgents(Agents):
    brief_type = BusinessBrief
    profile_type = BusinessProfile
    empty_profile = staticmethod(empty_profile)
    market_mode = True

    def discover(self, brief, feedback=""):
        sources = {}
        for query in (
            f"{brief.anchor_name} competitors alternatives {brief.country} {brief.goal}",
            f"{brief.goal} brands {brief.country} for {brief.audience} {feedback[:300]}",
        ):
            for source in self.search.search(query, "web", brief.news_days):
                sources[source.id] = source.model_dump()
        result = self.model.ask(Discovery,
            "Discover up to FIVE distinct competing brands for this business idea and reference brand. "
            "Use supplied evidence. Prefer comparable products and customers in the requested market. "
            "At this discovery stage, url may be the supporting evidence page; official websites will be resolved separately. Explain relevance with source IDs. "
            "Do not invent companies. Do not omit a supported brand merely because its official website is not yet known. If fewer than three brands are supported, return fewer. "
            "Use clarification only for genuine ambiguity, not missing pricing. Do not assume market share or local delivery.",
            {"brief": brief.model_dump(), "feedback": feedback, "sources": sources})
        accepted = []
        hosts = {urlparse(brief.anchor_url).hostname.removeprefix("www.").lower()}
        names = {brief.anchor_name.casefold()}
        blocked = {"owler.com", "tracxn.com", "crunchbase.com", "amazon.in", "amazon.com", "flipkart.com", "instagram.com", "facebook.com", "linkedin.com", "youtube.com", "wikipedia.org", "cbinsights.com", "zoominfo.com", "pitchbook.com"}
        for candidate in result.competitors[:5]:
            host = urlparse(candidate.url).hostname.removeprefix("www.").lower()
            valid_ids = [sid for sid in candidate.source_ids if sid in sources]
            if candidate.name.casefold() in names or not valid_ids:
                continue
            # Resolve every candidate independently; discovery URLs may be directories.
            resolved_sources = {}
            for source in self.search.search(candidate.name + " official website products", "web", brief.news_days):
                resolved_sources[source.id] = source.model_dump()
                sources[source.id] = source.model_dump()
            if not resolved_sources:
                continue
            resolved = self.model.ask(Candidate,
                "Resolve this brand's official HOME website using these search results. Never use a directory, marketplace or social account. "
                "Use a website hostname that occurs in the sources. Preserve the brand name and cite the evidence for the website.",
                {"brand":candidate.name,"sources":resolved_sources})
            candidate.url = resolved.url
            host = urlparse(candidate.url).hostname.removeprefix("www.").lower()
            if not any(host == urlparse(s["url"]).hostname.removeprefix("www.").lower() or host in s["text"].lower() for s in resolved_sources.values()):
                continue
            valid_ids += [sid for sid in resolved.source_ids if sid in resolved_sources]
            if host in hosts or host in blocked:
                continue
            candidate.source_ids = valid_ids
            accepted.append(candidate.model_dump())
            hosts.add(host)
            names.add(candidate.name.casefold())
            if len(accepted) == 3:
                break
        return accepted[:3], sources, result.clarification

    def plan_research(self, brief, company):
        host = urlparse(company["url"]).hostname.removeprefix("www.")
        return [
            {"query": f"{company['name']} products range ingredients services about brand", "kind": "web", "domains": [host]},
            {"query": f"{company['name']} positioning products prices {brief.country} {brief.audience}", "kind": "web"},
            {"query": f"{company['name']} product launch announcement news", "kind": "news"},
        ]

    def analyze(self, brief, company, sources):
        if not sources:
            return empty_profile(company["name"], company["url"], brief, "No usable source content.")
        # Keep provider token use bounded even when full pages are very large.
        ordered = sorted(sources.items(), key=lambda item: official_source(item[1]["url"], company["url"]), reverse=True)
        chosen = ordered[:3]
        chosen_ids = {sid for sid, _ in chosen}
        extra = next(((sid, src) for sid, src in ordered if sid not in chosen_ids and src.get("kind") == "news"), None)
        if extra is None:
            extra = next(((sid, src) for sid, src in ordered if sid not in chosen_ids), None)
        if extra:
            chosen.append(extra)
        sources = {sid: {**src, "text": src["text"][:8000]} for sid, src in chosen}
        profile = self.model.ask(BusinessProfile,
            "Research this brand using ONLY supplied sources. Extract positioning, up to 4 concrete products/services, "
            "up to 3 messaging claims, up to 2 published price examples (with product, currency, pack size if given), "
            "and up to 2 dated news items. Use short factual descriptions. Attribute marketing or health claims to the brand; "
            "do not endorse them as independently proven. Do not infer customer demand, market share, weaknesses, "
            "unserved needs, or nationwide availability. Pricing is optional and does not block other findings. "
            "Each claim must cite an EXACT contiguous source passage; copy Markdown as needed and never merge distant lines. "
            "For news require a source publication date within the lookback. Prefer primary sources. "
            "Use empty lists/null only for missing facts and explain material gaps briefly.",
            {"brief": brief.model_dump(), "company": company, "sources": sources})
        profile.name, profile.url = company["name"], company["url"]
        profile = validate_profile(profile, sources, brief)
        review = self.model.ask(EvidenceReview,
            "Check factual support. Return unsupported paths exactly from claim_fields. "
            "Reject invented details, misattributed brands, unsupported prices, and health promises stated as facts. "
            "An exact quote must entail the claim. Do not judge business suitability. "
            "Missing pricing or news does not invalidate supported product and positioning facts.",
            {"profile": profile.model_dump(), "claim_fields": {k:v.model_dump() for k,v in facts(profile).items()}, "sources": sources})
        return validate_profile(profile, sources, brief, review.rejected_fields)

    def followup(self, brief, profiles):
        weak = next((p for p in profiles.values() if not p.get("products") or not p.get("positioning")), None)
        if weak:
            return FollowUp(action="research", target_name=weak["name"],
                            query=f"site:{urlparse(weak['url']).hostname} {weak['name']} products about",
                            reason="Seek core product or positioning evidence.")
        return FollowUp(action="finish", target_name=None, query=None,
                        reason="Core competitor evidence collected; optional prices and news do not block synthesis.")

    def recommend(self, brief, profiles):
        catalog = {p.name:{field:claim.model_dump() for field,claim in facts(p).items()} for p in profiles}
        if not any(catalog.values()):
            return MarketPlan(explanation="No supported competitor facts were retrieved. Refine the reference brand or retry.",
                              opportunities=[], content_ideas=[], actions=[],
                              questions=["Provide an accessible reference brand website or narrow the market."])
        # Restrict synthesis references to actual checked facts in the JSON schema.
        lookup = {}
        flat_catalog = {}
        for company, fields in catalog.items():
            for field, claim in fields.items():
                fid = f"F{len(lookup)+1}"
                lookup[fid] = {"company": company, "field": field}
                flat_catalog[fid] = {"company": company, "claim": claim}
        allowed = Literal[tuple(lookup)]
        ref_type = create_model("AllowedFactReference", fact_id=(allowed, ...))
        experiment_type = create_model("GroundedExperiment", __base__=Experiment, basis=(list[ref_type], ...))
        content_type = create_model("GroundedContentIdea", __base__=ContentIdea, basis=(list[ref_type], ...))
        plan_type = create_model("GroundedMarketPlan", __base__=MarketPlan,
                                 opportunities=(list[experiment_type], Field(max_length=3)),
                                 content_ideas=(list[content_type], Field(max_length=5)))
        plan = self.model.ask(plan_type,
            "Create an actionable business research plan from this checked fact catalog. "
            "The user is PRE-LAUNCH: assume no products, testimonials, certifications or sales yet. "
            "Create marketing content for the USER'S proposed business, not advertisements for competitors. "
            "Use competitor facts as inspiration in basis only. Do not insert F-number identifiers in visible prose. "
            "Content formats should be short labels (Reel, carousel, poll, blog). CTAs should invite feedback or interest, "
            "not claim products exist or ask people to buy. Never invent testimonials or health benefits. "
            "Tests must be feasible as interviews, sketches, mockups or polls during the first week; do not require manufacturing or paid sales. "
            "Suggest 3 differentiation EXPERIMENTS, 5 promotional content ideas, and a 7-day action plan. "
            "Every experiment and content idea must cite at least one allowed fact_id from the catalog as basis. Explain the connection without claiming the idea is unique. "
            "Write proposals as things to try, not discoveries of unserved demand. "
            "Never invent statistics, preferences, competitor weaknesses, or guaranteed outcomes. "
            "Do not assert the user's product has certifications, ingredients or health benefits not provided. "
            "Content should explore or demonstrate potential offerings, with claims conditional on verification. "
            "Each experiment needs a cheap test and an observable success signal; label numeric thresholds as proposed targets. "
            "Actions must specify deliverables and align with the proposed experiments. Favor interviews, sketches and concept tests over manufacturing a finished product in one week. Questions should identify assumptions to validate.",
            {"brief": brief.model_dump(), "checked_facts": flat_catalog})
        data = plan.model_dump()
        for field in ("opportunities", "content_ideas"):
            for idea in data[field]:
                idea["basis"] = [lookup[ref["fact_id"]] for ref in idea["basis"]]
        return checked_plan(MarketPlan.model_validate(data), profiles)
