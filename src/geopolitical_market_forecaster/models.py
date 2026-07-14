from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field, HttpUrl


class SignalTier(str, Enum):
    actionable = "Actionable"
    fyi = "FYI"
    noise = "Noise"


class Confidence(str, Enum):
    low = "Low"
    medium = "Medium"
    high = "High"


class NewsItem(BaseModel):
    title: str
    source: str
    url: HttpUrl | str
    published_at: datetime | None = None
    region: str = "Middle East"
    summary: str | None = None
    raw_text: str | None = None
    collected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EconomicInsight(BaseModel):
    news_item: NewsItem
    signal_tier: SignalTier
    themes: list[str] = Field(default_factory=list)
    affected_markets: list[str] = Field(default_factory=list)
    rationale: str


class MarketForecast(BaseModel):
    insight: EconomicInsight
    forecast: str
    time_horizon: str
    confidence: Confidence
    evidence: list[str] = Field(default_factory=list)
    uncertainty: str


class GovernanceReview(BaseModel):
    forecast: MarketForecast
    approved: bool
    flags: list[str] = Field(default_factory=list)
    audit_notes: list[str] = Field(default_factory=list)


class PipelineResult(BaseModel):
    items_collected: int
    insights_created: int = 0
    forecasts_created: int = 0
    reviews_created: int = 0
    reviews: list[GovernanceReview]


class IngestionResult(BaseModel):
    source: str
    fetched: int
    inserted: int
    skipped: int
    errors: list[str] = Field(default_factory=list)
