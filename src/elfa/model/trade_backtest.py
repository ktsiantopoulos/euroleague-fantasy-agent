"""Replay past trade decisions under different trade-discipline settings.

For every matchday with a frozen pre-lock snapshot (decision_mdXX_locked.json + projection_mdXX_locked.csv)
and final platform points, re-run the optimiser from the same baseline squad, budget and trade allowance
with each setting, then score the recommended squad on actual points (roles as recommended, no in-round
swaps - same convention as the scorecard). The headline number is realised trade value: recommended squad
minus the no-trade squad, both on actual points, against what the optimiser predicted.
"""
from __future__ import annotations

import itertools
import json
from dataclasses import dataclass

import pandas as pd

from elfa.config import PROCESSED
from elfa.model.scorecard import actual_points, score
from elfa.optimise.lineup import optimise


@dataclass
class Case:
    matchday: int
    proj: pd.DataFrame
    budget: float
    baseline_ids: set[str]
    max_trades: int
    pts: dict[str, float]


def _squad(sol) -> list[dict]:
    return [{"platform_id": str(r.platform_id), "role": r.role, "captain": bool(r.captain)} for r in sol.squad.itertuples()]


def load_cases() -> list[Case]:
    cases = []
    for fp in sorted(PROCESSED.glob("decision_md*_locked.json")):
        md = int(fp.stem.split("md")[1].split("_")[0])
        pj = PROCESSED / f"projection_md{md:02d}_locked.csv"
        pts = actual_points(md)
        if not pj.exists() or not pts:
            continue
        dec = json.loads(fp.read_text(encoding="utf-8"))
        proj = pd.read_csv(pj, dtype={"platform_id": str})
        cases.append(Case(md, proj, float(dec["budget"]), {str(i) for i in dec["baseline_ids"]},
                          int(dec["trades_left"]), pts))
    return cases


def replay(case: Case, **kw) -> dict:
    hold = optimise(case.proj, case.budget, case.baseline_ids, case.max_trades, lock_squad=True)
    best = optimise(case.proj, case.budget, case.baseline_ids, case.max_trades, **kw)
    hold_act, best_act = score(_squad(hold), case.pts), score(_squad(best), case.pts)
    return {
        "matchday": case.matchday, **kw,
        "n_trades": len(best.trades_in), "trades_in": ", ".join(best.trades_in), "trades_out": ", ".join(best.trades_out),
        "pred_gain": round(best.expected_md_pts - hold.expected_md_pts, 1),
        "real_gain": round(best_act - hold_act, 1),
        "rec_actual": best_act, "hold_actual": hold_act,
    }


GRID = {
    "trade_hurdle": [0.0, 2.0, 3.0, 4.0, 6.0],
    "trade_sd_penalty": [0.0, 0.25, 0.5],
    "min_games_in": [1, 3],
}


def grid(cases: list[Case] | None = None, grid_def: dict | None = None) -> pd.DataFrame:
    cases = cases if cases is not None else load_cases()
    g = grid_def or GRID
    rows = []
    for combo in itertools.product(*g.values()):
        kw = dict(zip(g.keys(), combo))
        for c in cases:
            rows.append(replay(c, **kw))
    return pd.DataFrame(rows)


def summarise(df: pd.DataFrame) -> pd.DataFrame:
    keys = [k for k in GRID if k in df]
    return (df.groupby(keys)
              .agg(trades=("n_trades", "sum"), pred_gain=("pred_gain", "sum"), real_gain=("real_gain", "sum"))
              .reset_index().sort_values("real_gain", ascending=False))


def report() -> str:
    """Replay every frozen matchday: current defaults vs no discipline, plus the grid. Writes
    data/processed/trade_backtest.csv and trade_backtest.md."""
    from elfa.optimise import lineup as L

    cases = load_cases()
    if not cases:
        return "no matchday with a frozen pre-lock snapshot and final points yet"
    df = grid(cases)
    df.to_csv(PROCESSED / "trade_backtest.csv", index=False)
    now = dict(trade_hurdle=L.TRADE_HURDLE, trade_sd_penalty=L.TRADE_SD_PENALTY, min_games_in=L.MIN_GAMES_TRADE_IN)
    off = dict(trade_hurdle=0.0, trade_sd_penalty=0.0, min_games_in=1)
    lines = ["# Trade-discipline replay", "",
             f"Matchdays: {', '.join(str(c.matchday) for c in cases)} · realised gain = recommended squad minus no-trade squad, "
             "both on actual points", "", "| setting | MD | trades | predicted gain | realised gain |", "|---|---|---|---|---|"]
    for label, kw in (("current defaults", now), ("no discipline", off)):
        for c in cases:
            r = replay(c, **kw)
            lines.append(f"| {label} | {r['matchday']} | {r['n_trades']} | {r['pred_gain']:+.1f} | {r['real_gain']:+.1f} |")
    s = summarise(df)
    over = (df.pred_gain.sum() - df.real_gain.sum()) / max(df.n_trades.sum(), 1)
    lines += ["", f"Predicted trade gain overshoots realised by {over:.1f} pts per trade (all grid settings).", "",
              "Top grid settings by realised gain:", "", "```", s.head(5).to_string(index=False), "```"]
    txt = "\n".join(lines)
    (PROCESSED / "trade_backtest.md").write_text(txt, encoding="utf-8")
    return txt
