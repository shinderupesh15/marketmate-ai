import pytest
from market_research.market_schemas import *
from market_research.market_agents import MarketAgents, validate_profile, checked_plan, facts
from market_research.market_service import MarketService
from market_research.schemas import Claim, FollowUp, Source, utcnow
from market_research.reporting import render_report
from market_research.runtime import ServiceError

def sample(name="Reference"):
    c = Claim(text="The brand offers roasted snacks.", source_id="S1",
              quote="Our range includes roasted snacks for everyday breaks.")
    return BusinessProfile(name=name, url="https://example.com", positioning=c, products=[c],
                           messaging=[], pricing=[], news=[], gaps=[])

def test_missing_price_does_not_remove_product_evidence():
    p = sample()
    result = validate_profile(p, {"S1":{"text":p.products[0].quote}}, BusinessBrief())
    assert result.products and result.positioning
    assert result.pricing == []

def test_nested_rejection_and_false_quote_removed():
    p = sample()
    result = validate_profile(p, {"S1":{"text":p.products[0].quote}}, BusinessBrief(), ["products.0.text"])
    assert not result.products
    assert result.positioning
    assert not facts(validate_profile(p, {}, BusinessBrief()))

def test_unsupported_idea_basis_removed():
    p = sample()
    plan = MarketPlan(explanation="Invented summary", opportunities=[
        Experiment(title="Test", proposal="Try a sampler", basis=[FactRef(company="Invented",field="products.0")],
                   test="Interview people", success_signal="Interest")],content_ideas=[],actions=[],questions=[])
    checked = checked_plan(plan, [p])
    assert not checked.opportunities
    assert "Invented summary" not in checked.explanation

class FakeMarket(MarketAgents):
    def __init__(self, usage):
        self.usage = usage
        self.search = self
    def discover(self, brief, feedback=""):
        return [{"name":n,"url":"https://example.com","reason":"Fixture","source_ids":["S1"]} for n in ("Alpha","Beta","Gamma")],{},None
    def plan_research(self,*args):
        return [{"query":"fixture","kind":"web"}]
    def search(self,*args):
        return [Source(id="S1",url="https://example.com",title="Fixture",text=sample().products[0].quote,retrieved_at=utcnow())]
    def read_pages(self,*args):
        return []
    def analyze(self,brief,company,sources):
        return sample(company["name"])
    def followup(self,*args):
        return FollowUp(action="finish",target_name=None,query=None,reason="Fixture complete")
    def recommend(self,brief,profiles):
        return MarketPlan(explanation="Fixture supported research",opportunities=[],content_ideas=[],actions=[],questions=[])

# Avoid the attribute/method collision of the deliberately small fake provider.
class FakeSearch:
    def search(self,*args,**kwargs):
        return [Source(id="S1",url="https://example.com",title="Fixture",text=sample().products[0].quote,retrieved_at=utcnow())]
    def read_pages(self,*args):
        return []

def factory(usage):
    agent = FakeMarket(usage)
    agent.search = FakeSearch()
    return agent

def test_market_graph_review_and_export(tmp_path):
    service = MarketService(tmp_path, factory)
    run = service.new_run(BusinessBrief())
    state = service.execute(run)
    assert state["status"] == "review"
    assert len(state["profiles"]) == 4
    assert "products" in next(iter(state["profiles"].values()))
    with pytest.raises(PermissionError):
        service.export(run)
    report = render_report(state)
    assert "MarketMate AI" in report and "Competitor facts" in report
    service.execute(run, {"action":"approve"})
    assert (service.export(run)/"briefing.md").exists()

def test_revision_revokes_approval_and_returns_to_review(tmp_path):
    service = MarketService(tmp_path, factory)
    run = service.new_run(BusinessBrief())
    service.execute(run)
    state = service.execute(run, {"action":"revise","target_name":"Alpha","feedback":"Check products"})
    assert state["status"] == "review" and state["approved"] is False
    assert state["revision_count"] == 1

def test_synthesis_schema_restricts_references_to_checked_facts():
    class ModelStub:
        def ask(self, schema, task, payload):
            assert set(payload["checked_facts"]) == {"F1", "F2"}
            data = {"explanation":"Draft", "opportunities":[{
                "title":"Sampler experiment", "proposal":"Try a sampler", "basis":[{"fact_id":"F1"}],
                "test":"Show a mockup to potential customers", "success_signal":"Record which option people choose"}],
                "content_ideas":[], "actions":[], "questions":[]}
            import copy
            bad = copy.deepcopy(data)
            bad["opportunities"][0]["basis"][0]["fact_id"] = "Invented"
            from pydantic import ValidationError
            with pytest.raises(ValidationError):
                schema.model_validate(bad)
            return schema.model_validate(data)
    plan = MarketAgents(ModelStub(),None,None).recommend(BusinessBrief(),[sample()])
    assert plan.opportunities[0].basis[0].company == "Reference"
    assert plan.opportunities[0].basis[0].field == "positioning"

def test_analysis_context_is_bounded():
    from market_research.schemas import EvidenceReview
    class ModelStub:
        def ask(self, schema, task, payload):
            assert len(payload["sources"]) <= 4
            assert sum(len(s["text"]) for s in payload["sources"].values()) <= 32000
            if schema is BusinessProfile:
                return sample()
            return EvidenceReview(rejected_fields=[], notes=[])
    sources = {"S"+str(i):{"url":f"https://example.com/products/{i}",
               "text":sample().products[0].quote + "x"*20000,"kind":"web"} for i in range(12)}
    p=MarketAgents(ModelStub(),None,None).analyze(BusinessBrief(),{"name":"Reference","url":"https://example.com"},sources)
    assert p.products

def test_market_export_bypasses_legacy_renderer(tmp_path, monkeypatch):
    def legacy_renderer(_):
        raise AssertionError("MarketMate must not route through the CreatorKit renderer")
    monkeypatch.setattr("market_research.reporting.render_report", legacy_renderer)
    service = MarketService(tmp_path, factory)
    run = service.new_run(BusinessBrief())
    service.execute(run)
    with pytest.raises(PermissionError):
        service.export(run)
    service.execute(run, {"action":"approve"})
    assert "# MarketMate AI" in (service.export(run)/"briefing.md").read_text(encoding="utf-8")
