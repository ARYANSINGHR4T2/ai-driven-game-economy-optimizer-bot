import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import RobustScaler

from app.config import get_settings


MODEL_COLUMNS = [
    "total_events",
    "gold_generated",
    "net_gold",
    "trades",
    "unique_counterparties",
    "active_hours",
    "avg_abs_amount",
    "std_amount",
    "events_per_hour",
    "trade_ratio",
    "counterparty_density",
    "gold_per_level",
]


def score_players(features: pd.DataFrame) -> pd.DataFrame:
    if features.empty:
        return features

    scored = features.copy()
    X = scored.reindex(columns=MODEL_COLUMNS, fill_value=0).astype(float)

    if len(scored) < 10:
        scored["bot_risk_score"] = 0.0
        scored["flags"] = [[] for _ in range(len(scored))]
        return scored

    scaler = RobustScaler()
    X_scaled = scaler.fit_transform(X)
    model = IsolationForest(
        n_estimators=160,
        contamination=get_settings().anomaly_contamination,
        random_state=42,
    )
    model.fit(X_scaled)
    raw = -model.decision_function(X_scaled)
    risk = (raw - raw.min()) / max(raw.max() - raw.min(), 1e-9)
    scored["bot_risk_score"] = np.round(risk * 100, 2)
    scored["flags"] = scored.apply(_rule_flags, axis=1)
    return scored.sort_values("bot_risk_score", ascending=False)


def _rule_flags(row: pd.Series) -> list[str]:
    flags = []
    if row["events_per_hour"] > 8:
        flags.append("high_activity_rate")
    if row["active_hours"] > 18:
        flags.append("near_24h_activity")
    if row["gold_per_level"] > 1500:
        flags.append("wealth_outpaces_level")
    if row["trade_ratio"] > 0.55 and row["counterparty_density"] < 0.25:
        flags.append("repeated_trade_network")
    if row["gold_generated"] > 50000 and row["unique_counterparties"] <= 3:
        flags.append("farm_to_few_accounts")
    return flags
