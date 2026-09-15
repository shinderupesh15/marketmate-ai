"""MarketMate separates observed facts from proposed experiments."""

from pydantic import Field, field_validator

from market_research.schemas import Claim, Model, NewsItem, public_url


class BusinessBrief(Model):
    goal: str = Field(
        default="Launch an online healthy-snack brand for office workers",
        min_length=5,
        max_length=1000,
    )
    audience: str = Field(
        default="Office workers looking for convenient snacks", min_length=3, max_length=500
    )
    anchor_name: str = Field(default="The Whole Truth", min_length=1, max_length=100)
    anchor_url: str = "https://thewholetruthfoods.com"
    country: str = Field(default="India", min_length=2, max_length=80)
    news_days: int = Field(default=90, ge=7, le=365)
    _url = field_validator("anchor_url")(public_url)


class BusinessProfile(Model):
    name: str
    url: str
    positioning: Claim | None
    products: list[Claim]
    messaging: list[Claim]
    pricing: list[Claim]
    news: list[NewsItem]
    gaps: list[str]


class FactRef(Model):
    company: str
    field: str


class Experiment(Model):
    title: str
    proposal: str
    basis: list[FactRef]
    test: str
    success_signal: str


class ContentIdea(Model):
    title: str
    format: str
    outline: str
    call_to_action: str
    basis: list[FactRef]


class Action(Model):
    day: int = Field(ge=1, le=7)
    task: str
    deliverable: str


class MarketPlan(Model):
    explanation: str
    opportunities: list[Experiment] = Field(max_length=3)
    content_ideas: list[ContentIdea] = Field(max_length=5)
    actions: list[Action] = Field(max_length=7)
    questions: list[str]


def empty_profile(name, url, brief, reason):
    return BusinessProfile(
        name=name,
        url=url,
        positioning=None,
        products=[],
        messaging=[],
        pricing=[],
        news=[],
        gaps=[reason],
    )
