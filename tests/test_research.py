from pathlib import Path
from datetime import date
import httpx
import pytest
from market_research.schemas import *
from market_research.tools import YouSearch
from market_research.runtime import Usage, ServiceError, BudgetExceeded
from market_research.evidence import validate_passages, suitability, budget_check
from market_research.service import ResearchService
from market_research.reporting import export_report

def profile(name="Example", brief=None):
    brief = brief or CreatorBrief()
    c = Claim(text="Supported", source_id="S1", quote="The free plan supports Android in India without watermarks.")
    return Profile(name=name, url="https://example.com",
        price=Price(plan="Free", amount=0, currency="INR", interval="free",
                    taxes="included", mandatory_costs_known=True, evidence=c),
        positioning=c, features=[c], device=Verdict(status="meets", evidence=c),
        region=Verdict(status="meets", evidence=c),
        requirements=[Requirement(name=n, verdict=Verdict(status="meets", evidence=c)) for n in brief.must_haves],
        restrictions=[], news=[], gaps=[])

def test_quote_mismatch_removes_price_and_eligibility():
    p = profile()
    p.price.evidence = Claim(text="Free",source_id="S1",quote="An invented quotation which is absent")
    source = {"S1":{"text":"The free plan supports Android in India without watermarks."}}
    checked=validate_passages(p,source,CreatorBrief())
    assert checked.price.amount is None
    assert suitability(checked,CreatorBrief())["status"] == "unknown"

def test_missing_source_invalidates_feature():
    checked=validate_passages(profile(),{},CreatorBrief())
    assert not checked.features
    assert checked.device.status == "unknown"

@pytest.mark.parametrize("case,expected", [
    ("free","meets"), ("over_budget","does_not_meet"),
    ("yearly_not_allowed","does_not_meet"), ("yearly_allowed","meets"),
    ("foreign_currency","unknown"), ("tax_unknown","unknown"),
    ("extras_unknown","unknown"), ("device_unsupported","does_not_meet"),
    ("watermark_unknown","unknown"), ("region_unknown","unknown"),
])
def test_suitability_cases(case,expected):
    b=CreatorBrief()
    p=profile()
    if case not in ("free","device_unsupported","watermark_unknown","region_unknown"):
        p.price.interval="month"; p.price.amount=500
    if case=="over_budget": p.price.amount=1500
    if case.startswith("yearly"):
        p.price.interval="year"; p.price.amount=6000
        b.annual_ok=case=="yearly_allowed"
    if case=="foreign_currency": p.price.currency="USD"
    if case=="tax_unknown": p.price.taxes="unknown"
    if case=="extras_unknown": p.price.mandatory_costs_known=False
    if case=="device_unsupported": p.device.status="does_not_meet"
    if case=="watermark_unknown": p.requirements[0].verdict.status="unknown"
    if case=="region_unknown": p.region.status="unknown"
    assert suitability(p,b)["status"] == expected

def test_news_without_verified_date_is_removed():
    p=profile()
    p.news=[NewsItem(published_date=str(date.today()),evidence=p.features[0])]
    out=validate_passages(p,{"S1":{"text":p.features[0].quote,"published_at":None}},CreatorBrief())
    assert out.news == []

def test_retry_and_quota(tmp_path):
    statuses=iter([503,200])
    def handler(request):
        assert request.url.host=="ydc-index.io"
        return httpx.Response(next(statuses),json={"results":{"web":[],"news":[]}})
    usage=Usage(tmp_path/"u.sqlite","retry")
    search=YouSearch("fake",usage,httpx.MockTransport(handler),sleep=lambda _:None)
    assert search.search("test")==[]
    assert usage.counts()["search"]==2
    search=YouSearch("fake",usage,httpx.MockTransport(lambda r:httpx.Response(401)),sleep=lambda _:None)
    with pytest.raises(ServiceError,match="credentials"):
        search.search("test")

def test_budget_counts_survive_restart(tmp_path):
    db=tmp_path/"u.sqlite"
    Usage(db,"x",max_search=1).reserve("search")
    with pytest.raises(BudgetExceeded):
        Usage(db,"x",max_search=1).reserve("search")

class FakeAgents:
    def __init__(self,usage, fail=False):
        self.usage=usage
        self.fail=fail
        self.search=self
    def discover(self,brief,feedback):
        if self.fail: raise ServiceError("Fixture tool failure")
        return [{"name":n,"url":f"https://{n.lower()}.example.com","reason":"Fixture","source_ids":[]}
                for n in ["Alpha","Beta","Gamma"]],{},None
    def plan_research(self,brief,company):
        return [{"query":company["name"],"kind":"web"}]
    def search(self,*args): pass
    def analyze(self,brief,company,sources): return profile(company["name"],brief)
    def followup(self,*args):
        return FollowUp(action="finish",target_name=None,query=None,reason="Fixture coverage complete")
    def recommend(self,brief,profiles):
        return Recommendation(recommended_name=profiles[0].name,explanation="Fixture-only recommendation",tradeoffs=[],questions=[])

class FakeSearch:
    def search(self,*args):
        return [Source(id="S1",url="https://example.com",title="Fixture",
                       text="The free plan supports Android in India without watermarks.",retrieved_at=utcnow())]

def factory(usage):
    agents=FakeAgents(usage)
    agents.search=FakeSearch()
    return agents

def test_review_survives_restart_and_export_requires_approval(tmp_path):
    service=ResearchService(tmp_path,factory)
    rid=service.new_run(CreatorBrief())
    state=service.execute(rid)
    assert len(state["profiles"])==4
    assert state["status"]=="review"
    with pytest.raises(PermissionError): service.export(rid)
    restarted=ResearchService(tmp_path,factory)
    saved,pending,_=restarted.snapshot(rid)
    assert pending[0]["type"]=="review"
    assert len(saved["profiles"])==4
    approved=restarted.execute(rid,{"action":"approve"})
    assert approved["approved"] is True
    path=restarted.export(rid)
    assert (path/"briefing.md").exists()
    assert restarted.export(rid)==path

def test_revision_invalidates_draft_and_cancel_blocks_export(tmp_path):
    service=ResearchService(tmp_path,factory)
    rid=service.new_run(CreatorBrief())
    service.execute(rid)
    revised=service.execute(rid,{"action":"revise","target_name":"Alpha","feedback":"Check plan limits"})
    assert revised["status"]=="review" and not revised["approved"]
    assert revised["revision_count"]==1
    cancelled=service.execute(rid,{"action":"cancel"})
    assert cancelled["status"]=="cancelled"
    with pytest.raises(PermissionError): service.export(rid)

def test_failure_recovers_without_new_run(tmp_path):
    service=ResearchService(tmp_path,lambda u:FakeAgents(u,fail=True))
    rid=service.new_run(CreatorBrief())
    state=service.execute(rid)
    assert state["status"]=="needs_help"
    assert service.snapshot(rid)[1][0]["type"]=="recovery"
    resumed=ResearchService(tmp_path,factory).execute(rid,{"action":"retry"})
    assert resumed["status"]=="review"

def test_partial_report_after_failure(tmp_path):
    service=ResearchService(tmp_path,lambda u:FakeAgents(u,fail=True))
    rid=service.new_run(CreatorBrief())
    service.execute(rid)
    state=service.execute(rid,{"action":"partial"})
    assert state["status"]=="review"
    assert state["errors"]
    assert not state["approved"]

def test_budget_exhaustion_produces_partial_review(tmp_path):
    class ExhaustedSearch:
        def search(self, *args):
            raise BudgetExceeded("Search request budget reached.")
    def exhausted_factory(usage):
        a = factory(usage)
        a.search = ExhaustedSearch()
        return a
    service = ResearchService(tmp_path, exhausted_factory)
    rid = service.new_run(CreatorBrief())
    state = service.execute(rid)
    assert state["status"] == "review"
    assert not state["approved"]
    assert any("budget" in e for e in state["errors"])
    assert len(state["profiles"]) == 4

def test_summary_cannot_promote_unverified_gap_to_fact():
    from market_research.agents import Agents
    class NoModel:
        def ask(self, *args):
            raise AssertionError("No model choice needed when nothing qualifies")
    p = profile()
    p.region.status = "unknown"
    p.gaps = ["UNVERIFIED_RUMOR: the product has been banned"]
    result = Agents(NoModel(), None, None).recommend(CreatorBrief(), [p])
    assert result.recommended_name is None
    assert "banned" not in result.model_dump_json()
    assert "Verify Example is available in India" in " ".join(result.questions)
