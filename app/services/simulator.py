from dataclasses import dataclass
from datetime import datetime, timedelta
import random

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.db.models import MarketSnapshot, Player, Transaction


RESOURCES = ["gold", "iron", "crystal", "herbs", "rune"]


@dataclass
class SeedStats:
    players: int
    transactions: int
    market_snapshots: int


def reset_database(db: Session) -> None:
    db.execute(delete(Transaction))
    db.execute(delete(MarketSnapshot))
    db.execute(delete(Player))
    db.commit()


def seed_economy(db: Session, players: int = 500, days: int = 21, reset: bool = True) -> SeedStats:
    if reset:
        reset_database(db)

    rng = random.Random(42)
    created_players = []
    bot_ids = set(rng.sample(range(players), k=max(players // 20, 1)))
    whale_ids = set(rng.sample([i for i in range(players) if i not in bot_ids], k=max(players // 30, 1)))

    for i in range(players):
        segment = "bot_farm" if i in bot_ids else "whale" if i in whale_ids else rng.choice(["casual", "core", "trader"])
        player = Player(username=f"{segment}_{i:04d}", segment=segment, level=rng.randint(3, 80))
        db.add(player)
        created_players.append(player)
    db.flush()

    transactions = []
    start = datetime.utcnow() - timedelta(days=days)
    for day in range(days):
        day_at = start + timedelta(days=day)
        for player in created_players:
            event_count = _event_count(rng, player.segment)
            for _ in range(event_count):
                created_at = day_at + timedelta(hours=rng.randint(0, 23), minutes=rng.randint(0, 59))
                transactions.append(_make_transaction(rng, player, created_players, created_at))

    snapshots = []
    price_state = {"iron": 12.0, "crystal": 55.0, "herbs": 8.0, "rune": 120.0}
    for day in range(days):
        created_at = start + timedelta(days=day, hours=23)
        inflation_pressure = 1 + max(day - days * 0.45, 0) * 0.012
        for resource, base_price in price_state.items():
            shock = 1.0
            if resource == "crystal" and day > days * 0.6:
                shock += (day - days * 0.6) * 0.035
            median_price = base_price * inflation_pressure * shock * rng.uniform(0.95, 1.08)
            volume = rng.uniform(500, 3500) * (2.7 if resource == "crystal" and day > days * 0.75 else 1)
            snapshots.append(
                MarketSnapshot(
                    resource=resource,
                    median_price=round(median_price, 2),
                    volume=round(volume, 2),
                    listed_supply=round(rng.uniform(200, 1800), 2),
                    created_at=created_at,
                )
            )

    db.add_all(transactions)
    db.add_all(snapshots)
    db.commit()
    return SeedStats(players=len(created_players), transactions=len(transactions), market_snapshots=len(snapshots))


def _event_count(rng: random.Random, segment: str) -> int:
    if segment == "bot_farm":
        return rng.randint(18, 34)
    if segment == "whale":
        return rng.randint(5, 13)
    if segment == "trader":
        return rng.randint(4, 10)
    if segment == "core":
        return rng.randint(3, 8)
    return rng.randint(1, 5)


def _make_transaction(rng: random.Random, player: Player, players: list[Player], created_at: datetime) -> Transaction:
    if player.segment == "bot_farm":
        event_type = rng.choices(["bot_farm", "market_sell", "gift"], weights=[0.72, 0.18, 0.10])[0]
        amount = rng.uniform(180, 820) if event_type == "bot_farm" else rng.uniform(-900, -120)
        counterparty = rng.choice(players[: max(3, len(players) // 20)]).id if event_type in ["market_sell", "gift"] else None
        return Transaction(
            player_id=player.id,
            event_type=event_type,
            resource="gold",
            amount=round(amount, 2),
            counterparty_id=counterparty,
            price=None,
            quantity=None,
            created_at=created_at,
        )

    event_type = rng.choices(
        ["quest_reward", "loot_drop", "repair", "crafting_fee", "auction_tax", "market_buy", "market_sell"],
        weights=[0.32, 0.22, 0.12, 0.09, 0.06, 0.1, 0.09],
    )[0]
    resource = "gold" if event_type not in ["market_buy", "market_sell"] else rng.choice(RESOURCES[1:])
    sign = -1 if event_type in ["repair", "crafting_fee", "auction_tax", "market_buy"] else 1
    base = rng.uniform(15, 260) * (2.2 if player.segment == "whale" else 1)
    counterparty = rng.choice(players).id if event_type in ["market_buy", "market_sell"] else None
    quantity = rng.uniform(1, 25) if event_type in ["market_buy", "market_sell"] else None
    price = rng.uniform(5, 160) if quantity else None
    return Transaction(
        player_id=player.id,
        event_type=event_type,
        resource=resource,
        amount=round(sign * base, 2),
        counterparty_id=counterparty,
        price=round(price, 2) if price else None,
        quantity=round(quantity, 2) if quantity else None,
        created_at=created_at,
    )
