# Plan (mirror)

The authoritative, living plan is the shared Claude doc
"EuroLeague Fantasy Agent — Statistics Inventory & Phased Plan".
This file tracks phase status only.

| Phase | Status | Gate |
|---|---|---|
| P0 Data foundation | in progress | platform PIR == official PIR for MD 1–7 |
| P1 Baseline projection + optimiser | pending | backtest MAE beats platform avg_pts |
| P2 Matchup (DvP / PIRoE) | pending | DvP improves MAE, no variance increase |
| P3 Game-state & rotation (odds, PBP) | pending | odds term improves MAE on lopsided games |
| P4 Post-season reset | pending | ready before 16 Apr 2027 |

Decisions (24 Oct 2026): scheduled run one day before each deadline; odds in scope;
objective = PIR + μ·Δprice; rolling 3-matchday horizon (weights 1.0 / 0.6 / 0.3).
