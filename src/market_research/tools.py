"""You.com search tool. Credentials go only to the fixed provider endpoint."""
import hashlib
import time
from datetime import date, timedelta
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
from urllib.parse import urldefrag
import httpx
from market_research.schemas import Source, utcnow, public_url
from market_research.runtime import ServiceError

SEARCH_URL = "https://ydc-index.io/v1/search"

def retry_delay(header: str | None, attempt: int) -> float:
    if header:
        try:
            return max(0, float(header))
        except ValueError:
            try:
                return max(0, (parsedate_to_datetime(header) - datetime.now(timezone.utc)).total_seconds())
            except (ValueError, TypeError):
                pass
    return 2 ** attempt

class YouSearch:
    def __init__(self, key, usage, transport=None, sleep=time.sleep):
        self.key, self.usage, self.transport, self.sleep = key, usage, transport, sleep

    def search(self, query: str, kind="web", days=90) -> list[Source]:
        payload = {"query": query[:700], "count": 4}
        if kind == "news":
            payload["freshness"] = f"{date.today()-timedelta(days=days):%Y-%m-%d}to{date.today():%Y-%m-%d}"
        # Page extraction improves grounding while keeping the response bounded.
        payload["extraction"] = {"extraction_mode": "full_page"}
        with httpx.Client(timeout=35, transport=self.transport, follow_redirects=False) as client:
            for attempt in range(3):
                self.usage.reserve("search")
                try:
                    response = client.post(SEARCH_URL, headers={"X-API-Key": self.key},
                                           json=payload)
                except httpx.TransportError:
                    if attempt == 2:
                        raise ServiceError("You.com connection failed after three attempts.") from None
                    self.usage.record("retry", "You.com connection retry")
                    self.sleep(2 ** attempt)
                    continue
                if response.status_code in (429, 500, 502, 503, 504):
                    delay = retry_delay(response.headers.get("Retry-After"), attempt)
                    if attempt == 2 or delay > 20:
                        raise ServiceError(f"You.com temporarily unavailable (HTTP {response.status_code}); retry later.")
                    self.usage.record("retry", f"You.com HTTP {response.status_code}; retry")
                    self.sleep(delay)
                    continue
                if response.status_code in (401, 403, 402):
                    raise ServiceError("You.com credentials, permissions, or credits need attention.")
                if response.status_code != 200:
                    raise ServiceError(f"You.com rejected the search (HTTP {response.status_code}).")
                try:
                    data = response.json()
                except ValueError:
                    raise ServiceError("You.com returned an unreadable response.") from None
                return normalize(data, kind)
        return []

def normalize(data: dict, kind: str) -> list[Source]:
    result = []
    sections = data.get("results", {})
    if not isinstance(sections, dict):
        raise ServiceError("You.com response is missing its results object.")
    # News queries can return dated official announcements in the web section too.
    for section in ("web", "news"):
        rows = sections.get(section, [])
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            try:
                url = public_url(urldefrag(row.get("url", ""))[0])
            except ValueError:
                continue
            page = row.get("contents") or row.get("markdown") or row.get("raw_content")
            if isinstance(page, dict):
                page = page.get("markdown") or page.get("text")
            snippets = row.get("snippets", [])
            if not isinstance(snippets, list):
                snippets = []
            text = "\n".join(str(s) for s in [row.get("description", ""), *snippets, page or ""] if s)
            if not text.strip():
                continue
            digest = hashlib.sha256((url + text).encode()).hexdigest()[:14]
            result.append(Source(id="S"+digest, url=url, title=str(row.get("title", url)),
                                 text=text[:16000], retrieved_at=utcnow(),
                                 published_at=row.get("page_age") or row.get("published_date"),
                                 kind=section, content_level="page" if page else "excerpt"))
    return list({s.id:s for s in result}.values())
