"""Learn from each round: score past projections against actual platform points, find biases,
and adopt new parameters only when they beat the current ones out of sample.

Inputs: data/processed/projection_mdXX.csv (what we predicted before the matchday),
        data/raw/fantaking/fantasy_pts/<player>_mdXX.json (what actually happened).
Outputs: evaluation.csv (per player-matchday), evaluation.md (summary), params.json (if adopted).
"""
from __future__ import annotations

import json

import pandas as pd

from elfa.config import PROCESSED, RAW


def _actuals(md: int) -> pd.DataFrame:
    rows = []
    for fp in (RAW / "fantaking" / "fantasy_pts").glob(f"*_md{md:02d}.json"):
        j = json.loads(fp.read_text(encoding="utf-8"))
        if "error" in j:
            continue
        pid = fp.stem.split("_md")[0]
        rows.append({"platform_id": pid, "actual": j.get("fantasy_pts") if j.get("match") else 0.0,
                     "played": bool(j.get("match")) and (j.get("fantasy_pts") is not None)})
    return pd.DataFrame(rows)


def evaluate() -> tuple[pd.DataFrame, str]:
    parts = []
    # only snapshots frozen before the lock count: projection_mdXX.csv is rewritten by every run, including
    # post-lock and stale ones, so scoring it leaks results (MD 8 was scored against R9 fixtures that way)
    for fp in sorted(PROCESSED.glob("projection_md*_locked.csv")):
        md = int(fp.stem.split("md")[1].split("_")[0])
        act = _actuals(md)
        if act.empty:
            continue
        pr = pd.read_csv(fp, dtype={"platform_id": str})
        m = pr.merge(act, on="platform_id", how="inner")
        m["matchday"] = md
        parts.append(m)
    if not parts:
        return pd.DataFrame(), "no completed matchday with a pre-lock snapshot yet (first one: MD 9) - evaluation starts once it is played"
    df = pd.concat(parts, ignore_index=True)
    df["error"] = df.md_pts - df.actual
    df["abs_error"] = df.error.abs()
    df.to_csv(PROCESSED / "evaluation.csv", index=False)

    pl = df[(df.pos != "Head Coach") & (df.games_md > 0)]
    lines = ["# Projection evaluation", ""]
    for md, g in pl.groupby("matchday"):
        base = (g.avg_pts_platform.fillna(0) * g.games_md - g.actual).abs().mean()
        hi = (g.actual > g.md_p90).mean()
        lo = (g.actual < g.md_pts - (g.md_p90 - g.md_pts)).mean()
        lines.append(f"- MD{md}: {len(g)} players · MAE {g.abs_error.mean():.2f} (platform avg_pts baseline {base:.2f}) · bias {g.error.mean():+.2f} · "
                     f"corr {g[['md_pts','actual']].corr().iloc[0,1]:.3f} · above p90 {hi:.0%} / below p10 {lo:.0%} (target 10% each)")
    lines += ["", "## Bias by segment (mean projected − actual; positive = we over-project)"]
    seg = {
        "position": pl.groupby("pos").error.agg(["mean", "count"]),
        "projected minutes": pl.groupby(pd.cut(pl.min_hat, [0, 10, 20, 30, 50], labels=["<10", "10-20", "20-30", "30+"]), observed=True).error.agg(["mean", "count"]),
        "price": pl.groupby(pd.cut(pl.quotation, [0, 6, 9, 13, 30], labels=["≤6", "6-9", "9-13", "13+"]), observed=True).error.agg(["mean", "count"]),
        "availability": pl.groupby(pd.cut(pl.prob_play, [-0.01, 0.5, 0.99, 1.0], labels=["doubtful", "likely", "fit"]), observed=True).error.agg(["mean", "count"]),
    }
    for name, t in seg.items():
        lines.append(f"- {name}: " + ", ".join(f"{idx} {r['mean']:+.1f} (n={int(r['count'])})" for idx, r in t.iterrows()))
    worst = pl.sort_values("error").head(5)
    best = pl.sort_values("error", ascending=False).head(5)
    lines += ["", "## Biggest misses", "- under-projected: " + ", ".join(f"{r.name} ({r.md_pts:.0f}→{r.actual:.0f})" for r in worst.itertuples()),
              "- over-projected: " + ", ".join(f"{r.name} ({r.md_pts:.0f}→{r.actual:.0f})" for r in best.itertuples())]
    coach = df[df.pos == "Head Coach"]
    if len(coach):
        lines += ["", f"## Coaches: MAE {coach.abs_error.mean():.1f}, bias {coach.error.mean():+.1f} (n={len(coach)})"]
    txt = "\n".join(lines)
    (PROCESSED / "evaluation.md").write_text(txt, encoding="utf-8")
    return df, txt


def learn(pg: pd.DataFrame, schedule: list[dict], rounds: list[int]) -> str:
    """Guarded recalibration - see elfa.model.learning."""
    from elfa.model.learning import learn as _learn

    return _learn(pg, schedule, rounds)
