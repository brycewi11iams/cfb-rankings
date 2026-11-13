# College Football Ranking System

A personal college football ranking system built as a full data pipeline: API to Postgres to SQL views to Python ranking engines to Power BI.

I built a version of this in Excel last year and leaned heavily on AI to do it. This year I rebuilt it from scratch in SQL and Python, writing the code myself and designing the methods myself. The goal is a ranking system I can fully explain and call my own.

**Status: in progress.** The data pipeline, SQL views and the first ranking engine are done. The remaining engines and the Power BI dashboards are being built.

## How it works

```
CollegeFootballData API
        |
   Python ETL (requests, pandas)
        |
   PostgreSQL (teams, games, stats, engine_results)
        |
   SQL views (records, per-drive stats, strength of schedule)
        |
   Python ranking engines (pandas, numpy)
        |
   Power BI dashboards
```

## Ranking engines

The final ranking blends several engines with equal weights. Each engine takes an "as of week" input, so every week of the season has its own stored snapshot and past results never change.

| Engine | Status |
|---|---|
| KenPom-style (opponent-adjusted offense and defense) | Done, backfilled for 2025 and 2026 |
| Colley matrix | Planned |
| Massey (least squares) | Planned |
| Resume composite | Planned |
| Personal top 25 | Undecided |

### KenPom-style engine

Inspired by KenPom's college basketball ratings. For one team's side of one game, the model predicts points per drive:

```
expected = league average + team offense rating + opponent defense rating + home field term
```

- Every team gets an offense rating and a defense rating, both in points per drive above average.
- Ratings depend on each other (your offense rating needs your opponents' defense ratings), so they are solved by iterating until nothing changes by more than 0.0001.
- Home field advantage is estimated inside the model, not set by hand. It comes out around 3 to 4 points per game.
- FCS opponents are pooled into one tier and their games are down-weighted (0.5), because individual FCS teams play too few FBS games to rate on their own.
- Record and strength of schedule are display columns only, not inputs.

Early sanity check: for the 2025 season, four of the engine's top five matched the final poll's top five.

## Tech stack

- **Python:** requests, pandas, numpy, SQLAlchemy, psycopg2
- **Database:** PostgreSQL (DBeaver and pgAdmin for working in it)
- **SQL:** views for records, per-drive offense and defense, and strength of schedule
- **Visualization:** Power BI
- **Data:** [CollegeFootballData.com](https://collegefootballdata.com) API (free key required)
- **Tools:** Git, VS Code

## Repo layout

```
etl_games.py        pull games, team stats and drives from the API, clean, and load into Postgres
load_teams.py       load FBS and FCS teams
engine_kenpom.py    KenPom-style engine, plus storing results and backfilling every week
test_setup.py       checks the API key and the database connection
sql/schema.sql      table definitions
sql/views.sql       SQL views that the engines read from
requirements.txt    Python dependencies
```

## Setup

1. Clone the repo and create a virtual environment: `python -m venv .venv`
2. Install dependencies: `pip install -r requirements.txt`
3. Get a free API key from CollegeFootballData.com
4. Create a `.env` file in the repo root (it is gitignored):
   ```
   CFBD_API_KEY=your_key_here
   DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/cfb
   ```
5. Create a Postgres database called `cfb`, then run `sql/schema.sql`
6. Run `test_setup.py` to confirm the API and database both connect
7. Load teams, then load a season of games and stats with `load_season` in `etl_games.py`
8. Run `sql/views.sql`, then run the engine backfill in `engine_kenpom.py`

Raw API data is not stored in this repo. Each run pulls it fresh with your own key.

## Roadmap

- Power BI dashboard for each engine, then a combined page
- Colley and Massey engines
- Resume composite engine
- Combined blend and week-over-week comparison across all methods
- Later: shrink early-season ratings, tune the FCS weight, add tempo, and backtest each engine's predictions