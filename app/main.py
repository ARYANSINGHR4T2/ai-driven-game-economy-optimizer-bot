from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.analytics.anomaly import score_players
from app.analytics.economy import economy_metrics, market_alerts, resource_metrics
from app.analytics.features import player_feature_frame
from app.db.models import Player
from app.db.session import get_db, init_db
from app.schemas import (
    EconomyMetrics,
    MarketAlert,
    PlayerDetail,
    ResourceMetric,
    SeedRequest,
    SeedResponse,
    SuspiciousPlayer,
)
from app.services.simulator import seed_economy


app = FastAPI(title="AI-Driven Game Economy Optimizer", version="0.1.0")


@app.on_event("startup")
def startup() -> None:
      init_db()


@app.get("/health")
def health(db: Session = Depends(get_db)) -> dict[str, str]:
      db.execute(text("select 1"))
      return {"status": "ok", "database": "connected"}


@app.post("/seed", response_model=SeedResponse)
def seed(payload: SeedRequest, db: Session = Depends(get_db)) -> SeedResponse:
      stats = seed_economy(db, players=payload.players, days=payload.days, reset=payload.reset)
      return SeedResponse(**stats.__dict__)


@app.get("/metrics/economy", response_model=EconomyMetrics)
def get_economy_metrics(db: Session = Depends(get_db)) -> EconomyMetrics:
      return EconomyMetrics(**economy_metrics(db))


@app.get("/metrics/resources", response_model=list[ResourceMetric])
def get_resource_metrics(db: Session = Depends(get_db)) -> list[ResourceMetric]:
      return [ResourceMetric(**row) for row in resource_metrics(db)]


@app.get("/market/alerts", response_model=list[MarketAlert])
def get_market_alerts(db: Session = Depends(get_db)) -> list[MarketAlert]:
      return [MarketAlert(**row) for row in market_alerts(db)]


@app.get("/players/suspicious", response_model=list[SuspiciousPlayer])
def suspicious_players(limit: int = 25, db: Session = Depends(get_db)) -> list[SuspiciousPlayer]:
      features = score_players(player_feature_frame(db))
      if features.empty:
                return []
            rows = []
    for _, row in features.head(limit).iterrows():
              rows.append(
                            SuspiciousPlayer(
                                              player_id=int(row["player_id"]),
                                              username=str(row["username"]),
                                              segment=str(row["segment"]),
                                              bot_risk_score=float(row["bot_risk_score"]),
                                              flags=list(row["flags"]),
                                              gold_generated=float(row["gold_generated"]),
                                              trades=int(row["trades"]),
                                              unique_counterparties=int(row["unique_counterparties"]),
                            )
              )
          return rows


@app.get("/players/{player_id}", response_model=PlayerDetail)
def player_detail(player_id: int, db: Session = Depends(get_db)) -> PlayerDetail:
      player = db.get(Player, player_id)
    if player is None:
              raise HTTPException(status_code=404, detail="Player not found")

    features = score_players(player_feature_frame(db))
    row = features.loc[features["player_id"] == player_id]
    if row.empty:
              return PlayerDetail(
                            player_id=player.id,
                            username=player.username,
                            segment=player.segment,
                            level=player.level,
                            features={},
                            flags=[],
                            bot_risk_score=0,
              )
          record = row.iloc[0].to_dict()
    excluded = {"player_id", "username", "segment", "flags"}
    feature_values = {key: float(value) for key, value in record.items() if key not in excluded and isinstance(value, (int, float))}
    return PlayerDetail(
              player_id=player.id,
              username=player.username,
              segment=player.segment,
              level=player.level,
              features=feature_values,
              flags=list(record["flags"]),
              bot_risk_score=float(record["bot_risk_score"]),
    )
