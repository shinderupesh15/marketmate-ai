import json
import httpx
import pytest
from market_research.tools import YouSearch
from market_research.runtime import Usage, ServiceError, BudgetExceeded
from market_research.retrieval import select_sources

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

