# EuroLeague Fantasy Agent (elfa)

An agent that recommends the best EuroLeague Fantasy Challenge lineup for each matchday,
balancing projected PIR against budget growth over a rolling three-matchday horizon.

## How it works

```
platform API ─┐
official API ─┼─> ingest ─> features ─> projection ─> optimiser ─> report (email)
odds API ─────┘              (DvP, minutes, rate)     (ILP, 4 trades)
```

- **Scoring** is pure PIR; captain counts double.
- **Roster**: 11 slots = 4 G, 4 F, 2 C, 1 head coach; max 6 players per club; 4 trades per matchday.
- **Phases**: see `docs/plan.md` (mirrors the shared planning doc). Phase gates are backtests on played matchdays.

## Layout

```
src/elfa/
  ingest/     pull platform market/roster, official box scores, schedule, odds → data/raw
  features/   rolling minutes & PIR rate, pace, home/away, DvP / PIRoE, availability
  model/      projection (minutes × rate × adjustments), backtest harness
  optimise/   ILP lineup + trade optimiser (PuLP / OR-Tools)
  report/     recommendation report and email
data/
  raw/        JSON as fetched, one folder per matchday (gitignored)
  processed/  parquet feature tables (gitignored) + committed CSVs; matchdays.csv = matchday → round → game nights (turns), with the
              platform's turn split and deadline once seen (built by `elfa build`; the dashboard and the report read it first)
  prices/     price log, one CSV per matchday (committed); price_base.csv = season-start price per player (never overwritten)
  external/   slim copy of the Fantasy Edge IQ player CSV (season-start prices + cross-source check only; never a model input)
docs/
  data-sources.md   endpoints, IDs, rules, scoring (verified 24 Oct 2026)
tests/
notebooks/
```

## Setup

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env   # then fill in FANTAKING_TOKEN (see docs/data-sources.md §1)
```

## Secrets

Never commit `.env`. For the scheduled GitHub Actions relay, store `FANTAKING_TOKEN` and
`ODDS_API_KEY` as repository secrets.

## Status

Phase 0 — data foundation. First target: matchday 8 (= EuroLeague R8, two game nights), deadline 2026-10-27 15:59 UTC.
One fantasy matchday is one EuroLeague round; the platform's `num_rounds` counts the game nights (turns) inside it.

## Phase 0 run order (on your PC)

```bash
elfa pull-official                 # ~140 box scores, public API, a few minutes
elfa pull-platform --history       # market + roster + price log; --history adds per-player pts (358 × 7 calls)
elfa pull-external                 # Fantasy Edge IQ CSV -> data/external + price_base.csv (network; CI does this daily)
elfa build                         # player_games.parquet, maps, team_context / usage / fdr / matchdays CSVs, price_base fallback
elfa probe-trend                   # dump raw /trend /profile /upcoming-matches for 3 players (looking for a price series)
elfa reconcile                     # gate: platform pts == official PIR
```

## Dashboard

Two Streamlit apps share one page library (`app/pages_lib.py`) over the committed data:

| app | file | pages | audience |
|---|---|---|---|
| **Fantasy Agent** (private) | `app/streamlit_app.py` | Recommendation, What-if optimiser + all scouting pages | me — shows my squad, credits, trades, pipeline log |
| **Fantasy Scout** (shareable) | `app/scout_app.py` | Overview, Projections, Captain, Fixtures & schedule, Game script (odds), Defence vs position, Team context, Player, Top 100 managers, Market & prices, Model health | anyone picking players — never loads my roster/team files |

Locally: `pip install -r requirements.txt && streamlit run app/streamlit_app.py` (or `app/scout_app.py`).
Both are hosted on Streamlit Community Cloud from this repo (main branch) as two separate apps, one per main file.
