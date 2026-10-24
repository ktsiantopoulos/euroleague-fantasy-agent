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
  processed/  parquet/SQLite feature tables (gitignored)
  prices/     price log, one CSV per matchday (committed — not available historically)
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

Phase 0 — data foundation. First target: matchday 8 (double round), deadline 2026-10-27 15:59 UTC.
