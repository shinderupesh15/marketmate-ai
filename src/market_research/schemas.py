"""Contracts shared by the agents, UI, and checkpoint store."""
from datetime import datetime, timezone
from typing import Literal
from urllib.parse import urlparse
import ipaddress
from pydantic import BaseModel, ConfigDict, Field, field_validator

def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()

def public_url(value: str) -> str:
    p = urlparse(value.strip())
    host = p.hostname or ""
    if p.scheme not in ("http", "https") or not host or p.username or p.password:
        raise ValueError("Use a public http(s) website URL")
    if "." not in host or host.endswith((".local", ".internal")):
        raise ValueError("Use a public website")
    try:
        if not ipaddress.ip_address(host).is_global:
            raise ValueError("Private addresses are not supported")
    except ValueError as exc:
        if "Private" in str(exc):
            raise
    return value.strip()

class Model(BaseModel):
    model_config = ConfigDict(extra="forbid")

class CreatorBrief(Model):
    goal: str = Field(default="Instagram reels for my home bakery", min_length=5, max_length=1000)
    anchor_name: str = Field(default="Canva", min_length=1, max_length=100)
    anchor_url: str = "https://www.canva.com"
    country: str = Field(default="India", min_length=2, max_length=80)
    currency: str = Field(default="INR", pattern=r"^[A-Z]{3}$")
    device: str = Field(default="Android", min_length=1, max_length=80)
    monthly_budget: float = Field(default=1000, ge=0, le=1000000)
    annual_ok: bool = False
    experience: str = "Beginner"
    must_haves: list[str] = Field(default_factory=lambda: ["Watermark-free export"], max_length=6)
    news_days: int = Field(default=90, ge=1, le=365)
    _url = field_validator("anchor_url")(public_url)

class Source(Model):
    id: str
    url: str
    title: str
    text: str
    retrieved_at: str
    published_at: str | None = None
    kind: Literal["web", "news"] = "web"
    content_level: Literal["excerpt", "page"] = "excerpt"

class Claim(Model):
    text: str
    source_id: str
    quote: str

class Candidate(Model):
    name: str
    url: str
    reason: str
    source_ids: list[str]
    _url = field_validator("url")(public_url)

class Discovery(Model):
    competitors: list[Candidate]
    clarification: str | None

class SearchQuery(Model):
    query: str
    kind: Literal["web", "news"]

class SearchPlan(Model):
    queries: list[SearchQuery]

class Verdict(Model):
    status: Literal["meets", "does_not_meet", "unknown"]
    evidence: Claim | None

class Requirement(Model):
    name: str
    verdict: Verdict

class Price(Model):
    plan: str
    amount: float | None
    currency: str | None
    interval: Literal["free", "month", "year", "one_time", "unknown"]
    taxes: Literal["included", "excluded", "unknown"]
    mandatory_costs_known: bool
    evidence: Claim | None

class NewsItem(Model):
    published_date: str
    evidence: Claim

class Profile(Model):
    name: str
    url: str
    price: Price
    positioning: Claim | None
    features: list[Claim]
    device: Verdict
    region: Verdict
    requirements: list[Requirement]
    restrictions: list[Claim]
    news: list[NewsItem]
    gaps: list[str]

class EvidenceReview(Model):
    rejected_fields: list[str]
    notes: list[str]

class FollowUp(Model):
    action: Literal["research", "finish"]
    target_name: str | None
    query: str | None
    reason: str

class Recommendation(Model):
    recommended_name: str | None
    explanation: str
    tradeoffs: list[str]
    questions: list[str]

def unknown_profile(name: str, url: str, brief: CreatorBrief, reason: str) -> Profile:
    return Profile(
        name=name, url=url,
        price=Price(plan="Not verified", amount=None, currency=None, interval="unknown",
                    taxes="unknown", mandatory_costs_known=False, evidence=None),
        positioning=None, features=[], device=Verdict(status="unknown", evidence=None),
        region=Verdict(status="unknown", evidence=None),
        requirements=[Requirement(name=n, verdict=Verdict(status="unknown", evidence=None))
                      for n in brief.must_haves],
        restrictions=[], news=[], gaps=[reason],
    )
