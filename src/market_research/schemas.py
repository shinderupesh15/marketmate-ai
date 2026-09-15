"""Contracts shared by the agents, UI, and checkpoint store."""
from datetime import datetime, timezone
from typing import Literal
from urllib.parse import urlparse
import ipaddress
from pydantic import BaseModel, ConfigDict, field_validator

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


class NewsItem(Model):
    published_date: str
    evidence: Claim


class EvidenceReview(Model):
    rejected_fields: list[str]
    notes: list[str]


class FollowUp(Model):
    action: Literal["research", "finish"]
    target_name: str | None
    query: str | None
    reason: str
