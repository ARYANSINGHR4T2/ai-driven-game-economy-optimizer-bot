from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.models import MarketSnapshot
from app.analytics.features import transactions_frame


def gini(values: pd.Series) -> float:
    arr = np.array(values, dtype=float)
    if len(arr) == 0 or np.all(arr == 0):
        return 0.0
    arr = np.sort(arr - arr.min())
    total = arr.sum()
    if total == 0:
        return 0.0
    index = np.arange(1, arr.shape[0] + 1)
    return float((np.sum((2 * index - arr.shape[0] - 1) * arr)) / (arr.shape[0] * total))


def economy_metrics(db: Session) -> dict:
    df = transactions_frame(db, days=30)
    if df.empty:
        return {
            "total_currency_generated": 0,
            "total_currency_sunk": 0,
            "net_money_supply": 0,
            "marketplace_velocity": 0,
            "wealth_gini": 0,
            "inflation_7d": 0,
            "active_players": 0,
        }

    generated = df.loc[df["amount"] > 0, "amount"].sum()
    sunk = -df.loc[df["amount"] < 0, "amount"].sum()
    market_volume = df.loc[df["event_type"].isin(["market_buy", "market_sell"]), "amount"].abs().sum()
    balances = df.groupby("player_id")["amount"].sum()
    supply = float(generated - sunk)

    return {
        "total_currency_generated": round(float(generated), 2),
        "total_currency_sunk": round(float(sunk), 2),
        "net_money_supply": round(supply, 2),
        "marketplace_velocity": round(float(market_volume / max(abs(supply), 1)), 3),
        "wealth_gini": round(gini(balances), 3),
        "inflation_7d": round(inflation_rate(db, days=7), 3),
        "active_players": int(df["player_id"].nunique()),
    }


def resource_metrics(db: Session) -> list[dict]:
    df = transactions_frame(db, days=30)
    if df.empty:
        return []
    grouped = df.groupby("resource")
    rows = []
    for resource, item in grouped:
        generated = float(item.loc[item["amount"] > 0, "amount"].sum())
        sunk = float(-item.loc[item["amount"] < 0, "amount"].sum())
        rows.append({"resource": resource, "generated": generated, "sunk": sunk, "net": generated - sunk})
    return rows


def inflation_rate(db: Session, days: int = 7) -> float:
    cutoff = datetime.utcnow() - timedelta(days=days)
    stmt = select(MarketSnapshot).where(MarketSnapshot.created_at >= cutoff)
    rows = db.scalars(stmt).all()
    if not rows:
        return 0.0
    df = pd.DataFrame(
        {
            "resource": row.resource,
            "median_price": row.median_price,
            "created_at": row.created_at,
        }
        for row in rows
    )
    rates = []
    for _, item in df.groupby("resource"):
        ordered = item.sort_values("created_at")
        first = ordered["median_price"].iloc[0]
        last = ordered["median_price"].iloc[-1]
        if first > 0:
            rates.append((last - first) / first)
    return float(np.mean(rates)) if rates else 0.0


def market_alerts(db: Session) -> list[dict]:
    cutoff = datetime.utcnow() - timedelta(days=14)
    rows = db.scalars(select(MarketSnapshot).where(MarketSnapshot.created_at >= cutoff)).all()
    if not rows:
        return []
    df = pd.DataFrame(
        {
            "resource": row.resource,
            "median_price": row.median_price,
            "volume": row.volume,
            "created_at": row.created_at,
        }
        for row in rows
    )
    alerts = []
    threshold = get_settings().inflation_alert_threshold
    for resource, item in df.groupby("resource"):
        ordered = item.sort_values("created_at")
        if len(ordered) < 4:
            continue
        price_change = (ordered["median_price"].iloc[-1] - ordered["median_price"].iloc[0]) / max(ordered["median_price"].iloc[0], 1)
        recent_volume = ordered["volume"].tail(3).mean()
        baseline_volume = ordered["volume"].head(max(len(ordered) - 3, 1)).mean()
        if price_change > threshold:
            alerts.append(
                {
                    "resource": resource,
                    "alert_type": "hyper_inflation",
                    "severity": "critical" if price_change > threshold * 2 else "warning",
                    "message": f"{resource} median price rose {price_change:.1%} over the analysis window.",
                    "observed_value": float(price_change),
                    "created_at": ordered["created_at"].iloc[-1],
                }
            )
        if baseline_volume and recent_volume > baseline_volume * 2.5:
            alerts.append(
                {
                    "resource": resource,
                    "alert_type": "volume_spike",
                    "severity": "warning",
                    "message": f"{resource} trade volume is {recent_volume / baseline_volume:.1f}x baseline.",
                    "observed_value": float(recent_volume / baseline_volume),
                    "created_at": ordered["created_at"].iloc[-1],
                }
            )
    return alerts
