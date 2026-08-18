from app.analytics.anomaly import score_players
from app.analytics.economy import economy_metrics, market_alerts
from app.analytics.features import player_feature_frame
from app.db.session import SessionLocal, init_db
from app.services.simulator import seed_economy


def test_seed_and_score_pipeline():
    init_db()
    with SessionLocal() as db:
        seed_economy(db, players=80, days=8, reset=True)
        metrics = economy_metrics(db)
        features = player_feature_frame(db)
        scored = score_players(features)
        alerts = market_alerts(db)

    assert metrics["active_players"] == 80
    assert not features.empty
    assert "bot_risk_score" in scored.columns
    assert scored["bot_risk_score"].max() >= scored["bot_risk_score"].min()
    assert isinstance(alerts, list)
