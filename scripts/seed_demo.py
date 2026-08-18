import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.session import SessionLocal, init_db
from app.services.simulator import seed_economy


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed a simulated multiplayer economy.")
    parser.add_argument("--players", type=int, default=500)
    parser.add_argument("--days", type=int, default=21)
    parser.add_argument("--append", action="store_true", help="Append data instead of resetting tables.")
    args = parser.parse_args()

    init_db()
    with SessionLocal() as db:
        stats = seed_economy(db, players=args.players, days=args.days, reset=not args.append)
    print(f"Seeded {stats.players} players, {stats.transactions} transactions, {stats.market_snapshots} market snapshots.")


if __name__ == "__main__":
    main()
