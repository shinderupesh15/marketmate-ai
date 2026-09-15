
import json
import httpx
import pytest
from test_research import profile
from market_research.schemas import CreatorBrief
from market_research.evidence import validate_passages, suitability
from market_research.retrieval import select_sources
from market_research.tools import YouSearch
from market_research.runtime import Usage, ServiceError

def test_partial_pricing_retains_base_and_billing():
    p = profile()
    p.price.plan, p.price.amount, p.price.interval = "Pro", 500, "month"
    p.price.evidence.quote = "Pro costs INR 500 per month."
    checked = validate_passages(p, {"S1": {"text": p.price.evidence.quote}}, CreatorBrief(),
                                ["price.taxes", "price.mandatory_costs_known"])
    assert (checked.price.plan, checked.price.amount, checked.price.currency, checked.price.interval) == ("Pro", 500, "INR", "month")
    fit = suitability(checked, CreatorBrief())
    assert fit["published_price_status"] == "meets"
    assert fit["budget_status"] == "unknown"

def test_rejected_amount_keeps_supported_plan_and_interval():
    p = profile()
    checked = validate_passages(p, {"S1": {"text": p.price.evidence.quote}}, CreatorBrief(), ["price.amount"])
    assert checked.price.amount is None
    assert checked.price.plan == "Free"
    assert checked.price.interval == "free"

def test_pricing_survives_later_news():
    sources = {"price": {"url": "https://example.com/pricing", "text": "Published plans", "retrieved_at": "2026-01-01", "kind": "web"}}
    sources.update({str(i): {"url": f"https://news.example.org/{i}", "text": "News", "retrieved_at": "2026-09-01", "kind": "news"} for i in range(20)})
    selected = select_sources(list(sources), sources, "https://example.com")
    assert "price" in selected
    assert len(selected) == 12

def test_direct_page_and_domain_filter(tmp_path):
    requests = []
    def handler(request):
        requests.append(json.loads(request.content))
        if request.url.path.endswith("contents"):
            return httpx.Response(200, json=[{"url": "https://example.com/pricing", "markdown": "Pro is INR 500 monthly.", "title": "Plans"}])
        return httpx.Response(200, json={"results": {"web": []}})
    search = YouSearch("fake", Usage(tmp_path/"u.sqlite", "x"), httpx.MockTransport(handler))
    search.search("pricing", domains=["example.com"])
    pages = search.read_pages(["https://example.com/pricing"])
    assert requests[0]["include_domains"] == ["example.com"]
    assert pages[0].content_level == "page"
    assert pages[0].published_at is None
    assert pages[0].text == "Pro is INR 500 monthly."

def test_bad_contents_response_is_safe_error(tmp_path):
    search = YouSearch("fake", Usage(tmp_path/"u.sqlite", "x"),
                       httpx.MockTransport(lambda r: httpx.Response(200, json={})))
    with pytest.raises(ServiceError, match="page response"):
        search.read_pages(["https://example.com/pricing"])

def test_nested_reviewer_paths_remove_verdicts():
    p = profile()
    checked = validate_passages(p, {"S1": {"text": p.price.evidence.quote}}, CreatorBrief(),
                                ["device.status", "requirements.0.verdict.status"])
    assert checked.device.status == "unknown"
    assert checked.requirements[0].verdict.status == "unknown"
