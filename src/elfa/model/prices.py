"""Platform price dynamics: how a player's quotation moves from one matchday to the next.

Fitted on the committed price log (data/prices/md_XX.csv) joined to the per-player platform points
(data/raw/fantaking/fantasy_pts). MD 8→11 (1,075 player-transitions): the move is almost entirely last
round's score relative to the player's season average,

    Δprice ≈ 0.03 × (pts − avg_pts)        R² 0.72

Popularity and its change add nothing once that excess is in, and the slope is stable across the three
transitions. A DNP counts as 0 points, so an injured player who is held loses ~0.6 credits a round.

`expected_price_change` turns our projection into an expected budget move over the optimiser's horizon,
which the ILP values at MU_PRICE expected points per credit ("ride the market": buy rising players,
sell falling ones, grow the budget for later rounds).
"""
from __future__ import annotations

import glob
import json
from itertools import pairwise
from pathlib import Path

import numpy as np
import pandas as pd

from elfa.config import PRICES, PROCESSED, RAW

DEFAULT_SLOPE = 0.03        # credits per point of excess over season average (fallback before any fit)
MIN_PAIRS = 200             # refit only with at least this many player-transitions
HORIZON_DECAY = 0.9         # excess shrinks as the season average absorbs each new result (~1/n, n≈10 games)
HORIZON_MDS = 3             # same horizon as the optimiser (this matchday + two more)
MODEL_FP = PROCESSED / "price_model.json"


def _platform_pts() -> dict[tuple[int, int], float]:
    out: dict[tuple[int, int], float] = {}
    for fp in glob.glob(str(RAW / "fantaking" / "fantasy_pts" / "*.json")):
        stem = Path(fp).stem
        try:
            pid, md = stem.split("_md")
            d = json.loads(Path(fp).read_text(encoding="utf-8"))
        except (ValueError, json.JSONDecodeError):
            continue
        v = d.get("fantasy_pts")
        if v is not None:
            out[(int(pid), int(md))] = float(v)
    return out


def price_pairs() -> pd.DataFrame:
    """One row per (player, matchday→next matchday) with the price move and that matchday's excess score."""
    files = sorted(PRICES.glob("md_*.csv"))
    snaps: dict[int, pd.DataFrame] = {}
    for fp in files:
        try:
            md = int(fp.stem.split("_")[1])
        except (IndexError, ValueError):
            continue
        df = pd.read_csv(fp).drop_duplicates("player_id").set_index("player_id")
        df["quotation"] = pd.to_numeric(df.quotation, errors="coerce")
        df["avg_pts"] = pd.to_numeric(df.avg_pts, errors="coerce")
        snaps[md] = df
    pts = _platform_pts()
    rows = []
    mds = sorted(snaps)
    for a, b in pairwise(mds):
        if b != a + 1:
            continue    # a gap in the log would mix several rounds of movement into one pair
        A, B = snaps[a], snaps[b]
        for pid in A.index.intersection(B.index):
            qa, qb = A.at[pid, "quotation"], B.at[pid, "quotation"]
            sc = pts.get((int(pid), a))
            if pd.isna(qa) or pd.isna(qb) or sc is None or pd.isna(A.at[pid, "avg_pts"]):
                continue
            rows.append({"player_id": int(pid), "matchday": a, "price": float(qa), "dprice": round(float(qb - qa), 2),
                         "pts": sc, "avg_pts": float(A.at[pid, "avg_pts"])})
    df = pd.DataFrame(rows)
    if len(df):
        df["excess"] = df.pts - df.avg_pts
    return df


def fit_price_model(write: bool = True) -> dict:
    """Δprice = intercept + slope × excess, least squares on the price log. Falls back to DEFAULT_SLOPE."""
    pairs = price_pairs()
    model = {"slope": DEFAULT_SLOPE, "intercept": 0.0, "r2": None, "n": len(pairs), "matchdays": [], "fitted": False}
    if len(pairs) >= MIN_PAIRS:
        X = np.c_[np.ones(len(pairs)), pairs.excess.values]
        y = pairs.dprice.values
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        pred = X @ beta
        ss_res = float(((y - pred) ** 2).sum())
        ss_tot = float(((y - y.mean()) ** 2).sum()) or 1.0
        model.update(intercept=round(float(beta[0]), 4), slope=round(float(beta[1]), 4), r2=round(1 - ss_res / ss_tot, 3),
                     matchdays=sorted(int(m) for m in pairs.matchday.unique()), fitted=True)
    if write:
        MODEL_FP.write_text(json.dumps(model, indent=2), encoding="utf-8")
    return model


def load_price_model() -> dict:
    if MODEL_FP.exists():
        try:
            return json.loads(MODEL_FP.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return fit_price_model(write=True)


def expected_price_change(proj: pd.DataFrame, model: dict | None = None, horizon_mds: int = HORIZON_MDS,
                          decay: float = HORIZON_DECAY) -> dict[str, float]:
    """platform_id -> expected credits gained (or lost) over the horizon if the player is held.

    This matchday's expected excess is `md_pts - avg_pts_platform` (a player without a game moves nothing);
    later matchdays reuse that excess shrunk by `decay` each round, since the season average catches up.
    Coaches have no market price dynamics worth modelling and get 0."""
    m = model or load_price_model()
    slope, icpt = float(m.get("slope", DEFAULT_SLOPE)), float(m.get("intercept", 0.0))
    mult = sum(decay ** k for k in range(horizon_mds))
    out: dict[str, float] = {}
    avg_col = "avg_pts_platform" if "avg_pts_platform" in proj else None
    for r in proj.itertuples():
        if r.pos == "Head Coach" or avg_col is None:
            out[r.platform_id] = 0.0
            continue
        avg = getattr(r, avg_col)
        games = getattr(r, "games_md", 1)
        if pd.isna(avg) or not games:
            out[r.platform_id] = 0.0
            continue
        excess = float(r.md_pts) - float(avg)
        out[r.platform_id] = round((icpt + slope * excess) * mult, 3)
    return out


def summary(model: dict) -> str:
    if not model.get("fitted"):
        return f"price model: default slope {model.get('slope', DEFAULT_SLOPE)} (only {model.get('n', 0)} pairs logged)"
    return (f"price model: Δprice = {model['intercept']:+.3f} + {model['slope']:.4f} × (pts − avg) · "
            f"R² {model['r2']} · n {model['n']} · MD {model['matchdays'][0]}→{model['matchdays'][-1] + 1}")
