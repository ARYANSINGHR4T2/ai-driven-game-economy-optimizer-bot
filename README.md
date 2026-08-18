# AI-Driven Game Economy Optimizer & Bot Predictor

Backend analytics for multiplayer game economies: transaction monitoring, inflation detection, and bot-risk scoring for simulated player markets.

## What It Does

- Simulates MMO-style players, resource generation, marketplace trades, and suspicious gold-farming behavior.
- Stores economic events in a relational database through SQLAlchemy.
- Exposes a FastAPI service for health metrics, bot predictions, market alerts, and data seeding.
- Uses Pandas and Scikit-learn anomaly detection to flag likely bots and economy instability.
- Provides a Streamlit live-ops dashboard for economy health, inflation, wealth concentration, and suspicious accounts.

## Quick Start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts\seed_demo.py --players 500 --days 21
uvicorn app.main:app --reload
```

In a second terminal:

```powershell
streamlit run dashboard\streamlit_app.py
```

FastAPI docs: http://127.0.0.1:8000/docs

## PostgreSQL

The app defaults to `sqlite:///./game_economy.db` for local demos. To use PostgreSQL:

```powershell
$env:DATABASE_URL="postgresql+psycopg://game_ops:password@localhost:5432/game_economy"
python scripts\seed_demo.py
uvicorn app.main:app --reload
```

## Key Endpoints

- `GET /health` - service and database status
- `POST /seed` - generate a fresh simulated economy
- `GET /metrics/economy` - aggregate money supply, inflation, velocity, concentration
- `GET /metrics/resources` - faucet and sink balance by resource
- `GET /market/alerts` - hyper-inflation and volume anomalies
- `GET /players/suspicious` - bot-risk ranking
- `GET /players/{player_id}` - player profile and risk features

## Project Layout

```text
app/
  analytics/       anomaly detection, economy metrics, feature engineering
  db/              SQLAlchemy session and ORM models
  services/        simulation and orchestration
  main.py          FastAPI app
dashboard/         Streamlit frontend
scripts/           demo seeding tools
tests/             lightweight regression tests
```
