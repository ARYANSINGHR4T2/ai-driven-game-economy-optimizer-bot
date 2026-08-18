from datetime import datetime

from pydantic import BaseModel


class EconomyMetrics(BaseModel):
    total_currency_generated: float
    total_currency_sunk: float
    net_money_supply: float
    marketplace_velocity: float
    wealth_gini: float
    inflation_7d: float
    active_players: int


class ResourceMetric(BaseModel):
    resource: str
    generated: float
    sunk: float
    net: float


class MarketAlert(BaseModel):
    resource: str
    alert_type: str
    severity: str
    message: str
    observed_value: float
    created_at: datetime


class SuspiciousPlayer(BaseModel):
    player_id: int
    username: str
    segment: str
    bot_risk_score: float
    flags: list[str]
    gold_generated: float
    trades: int
    unique_counterparties: int


class PlayerDetail(BaseModel):
    player_id: int
    username: str
    segment: str
    level: int
    features: dict[str, float]
    flags: list[str]
    bot_risk_score: float


class SeedRequest(BaseModel):
    players: int = 500
    days: int = 21
    reset: bool = True


class SeedResponse(BaseModel):
    players: int
    transactions: int
    market_snapshots: int
