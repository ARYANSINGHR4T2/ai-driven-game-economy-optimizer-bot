# AI-Driven Game Economy Optimizer & Bot Predictor

I built this over a few weekends after arguing with an old MMO guild about who was farming gold with bots and why prices kept spiking out of nowhere. It's a backend that simulates a small in-game economy and then tries to flag the accounts that look like bots, plus catch inflation before it wrecks the market.

It's not hooked up to a real game - everything is simulated (random players, trades, farming behavior) so I could test the analytics without needing an actual live economy to pull data from.

## What's actually in here

- A FastAPI backend that stores everything in a database (SQLite by default so you don't have to set up Postgres just to try it, but Postgres works fine too if you swap the connection string)
- A simulator that generates fake players - casuals, traders, whales, and a chunk of "bot farm" accounts that behave differently on purpose
- Anomaly detection with scikit-learn (Isolation Forest) plus a few manual rule-based flags I added because the model alone missed some obvious cases
- A Streamlit dashboard so I could actually look at charts instead of staring at JSON responses all day

## Running it locally

I used PowerShell for all of this since I'm on Windows - adjust if you're on something else:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts\seed_demo.py --players 500 --days 21
uvicorn app.main:app --reload
```

Then in a second terminal:

```powershell
streamlit run dashboard\streamlit_app.py
```

API docs show up at http://127.0.0.1:8000/docs once it's running.

## Using Postgres instead of SQLite

By default it just writes to a local `game_economy.db` file so there's nothing to configure. If you want Postgres instead:

```powershell
$env:DATABASE_URL="postgresql+psycopg://game_ops:password@localhost:5432/game_economy"
python scripts\seed_demo.py
uvicorn app.main:app --reload
```

## Endpoints

- `GET /health` - checks the DB connection is alive
- `POST /seed` - wipes and regenerates a fresh simulated economy
- `GET /metrics/economy` - money supply, inflation, velocity, wealth concentration (Gini)
- `GET /metrics/resources` - how much of each resource is being generated vs sunk
- `GET /market/alerts` - flags weird price/volume spikes
- `GET /players/suspicious` - ranked list of accounts most likely to be bots
- `GET /players/{player_id}` - single player breakdown

## Layout

```text
app/
  analytics/       bot detection + economy math
  db/               models and session handling
  services/         the simulator that fakes the economy
  main.py           FastAPI routes
dashboard/          Streamlit charts
scripts/             CLI seeding script
tests/               a couple of sanity checks, not full coverage
```

## Stuff I still want to fix

- The bot detection is honestly still pretty rough - it catches obvious farming patterns but a smarter bot would probably slip through. I want to try adding time-of-day / session-length features at some point.
- No auth on the API at all right now, it's just for local testing.
- The dashboard could use loading states - right now it just kind of blanks out while it fetches.
- Tests only cover the happy path.

Started this mostly to see how anomaly detection actually holds up on synthetic data before trying it on something real. Feedback and issues welcome!
