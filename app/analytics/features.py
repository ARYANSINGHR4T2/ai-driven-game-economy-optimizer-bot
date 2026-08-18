from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Player, Transaction


def transactions_frame(db: Session, days: int | None = None) -> pd.DataFrame:
    stmt = select(Transaction, Player.username, Player.segment, Player.level).join(Player)
    if days is not None:
        stmt = stmt.where(Transaction.created_at >= datetime.utcnow() - timedelta(days=days))
    rows = db.execute(stmt).all()
    records = []
    for tx, username, segment, level in rows:
        records.append(
            {
                "id": tx.id,
                "player_id": tx.player_id,
                "username": username,
                "segment": segment,
                "level": level,
                "event_type": tx.event_type,
                "resource": tx.resource,
                "amount": tx.amount,
                "counterparty_id": tx.counterparty_id,
                "price": tx.price,
                "quantity": tx.quantity,
                "created_at": tx.created_at,
            }
        )
    return pd.DataFrame.from_records(records)


def player_feature_frame(db: Session, days: int = 14) -> pd.DataFrame:
    df = transactions_frame(db, days=days)
    if df.empty:
        return pd.DataFrame()

    df["is_trade"] = df["event_type"].isin(["market_buy", "market_sell", "gift"])
    df["is_generation"] = df["event_type"].isin(["quest_reward", "loot_drop", "bot_farm"])
    df["is_sink"] = df["event_type"].isin(["repair", "crafting_fee", "auction_tax"])
    df["hour"] = pd.to_datetime(df["created_at"]).dt.hour
    df["generated_amount"] = np.where(df["is_generation"], df["amount"].clip(lower=0), 0)
    df["sunk_amount"] = np.where(df["is_sink"], -df["amount"].clip(upper=0), 0)
    df["abs_amount"] = df["amount"].abs()

    grouped = df.groupby(["player_id", "username", "segment", "level"], dropna=False)
    features = grouped.agg(
        total_events=("id", "count"),
        gold_generated=("generated_amount", "sum"),
        gold_sunk=("sunk_amount", "sum"),
        net_gold=("amount", "sum"),
        trades=("is_trade", "sum"),
        unique_counterparties=("counterparty_id", "nunique"),
        active_hours=("hour", "nunique"),
        avg_abs_amount=("abs_amount", "mean"),
        std_amount=("amount", lambda s: float(np.std(s))),
    ).reset_index()

    play_span = grouped["created_at"].agg(lambda s: max((s.max() - s.min()).total_seconds() / 3600, 1)).reset_index(name="observed_hours")
    features = features.merge(play_span, on=["player_id", "username", "segment", "level"])
    features["events_per_hour"] = features["total_events"] / features["observed_hours"]
    features["trade_ratio"] = features["trades"] / features["total_events"].clip(lower=1)
    features["counterparty_density"] = features["unique_counterparties"] / features["trades"].clip(lower=1)
    features["gold_per_level"] = features["gold_generated"] / features["level"].clip(lower=1)
    return features.fillna(0)
