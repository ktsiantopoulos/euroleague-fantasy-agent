# Plan (mirror)

The authoritative, living plan is the shared Claude doc
"EuroLeague Fantasy Agent — Statistics Inventory & Phased Plan".
This file tracks phase status only.

| Phase | Status | Gate |
|---|---|---|
| P0 Data foundation | **passed 24 Oct** (2,474 player-games, scoring = PIR + 10% win bonus; bench 50%; coach margin buckets) | platform PIR == official PIR for MD 1–7 |
| P1 Baseline projection + optimiser | **passed 24 Oct** (MAE 5.52 vs 5.82 season-mean, R4–7) | backtest MAE beats season-mean baseline |
| P2 Matchup (DvP / PIRoE) | **in model** (γ=1.0 best in grid; this season only, league-mean shrinkage) | DvP improves MAE, no variance increase |
| P3 Game-state & rotation (odds, PBP) | odds hook live, waiting for ODDS_API_KEY secret; PBP later | odds term improves MAE on lopsided games |
| P4 Post-season reset | pending | ready before 16 Apr 2027 |

Decisions (24 Oct 2026): scheduled run one day before each deadline; odds in scope;
objective = PIR + μ·Δprice; rolling 3-matchday horizon (weights 1.0 / 0.6 / 0.3).
