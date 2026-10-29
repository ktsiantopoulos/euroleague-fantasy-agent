"""Self-correction layers fitted on the walk-forward backtest (each round predicted only from earlier rounds,
so nothing here sees the result it is scored on).

- calibration: are the uncertainty bands honest? coverage of the 80% interval and an sd scale factor;
- bias:        shrunk, recency-weighted multipliers per (position x projected-minutes band);
- attribution: how much of each miss is a minutes miss vs a per-minute (rate) miss.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from elfa.model.projection import minutes_band

Z80 = 1.2816
BIAS_PRIOR_N = 60.0      # a segment needs ~60 player-games before its own ratio gets half the weight
BIAS_DECAY = 0.7         # per-round weight decay: last round 1.0, the one before 0.7, ...
BIAS_CLIP = (0.85, 1.15)
SD_CLIP = (0.7, 1.6)


def _dressed(t: pd.DataFrame) -> pd.DataFrame:
    return t[(t.actual_min > 0) | (t.min_hat >= 5)].copy()


# ---------- calibration ----------
def calibration(t: pd.DataFrame) -> dict:
    t = _dressed(t)
    t = t[t.sd > 0]
    z = (t.actual_pir - t.model) / t.sd
    k = float(np.quantile(np.abs(z), 0.8) / Z80) if len(z) else 1.0
    return {
        "n": int(len(t)),
        "above_p90": round(float((z > Z80).mean()), 3),
        "below_p10": round(float((z < -Z80).mean()), 3),
        "inside_80": round(float((np.abs(z) <= Z80).mean()), 3),
        "z_sd": round(float(z.std()), 3),
        "sd_scale": round(float(np.clip(k, *SD_CLIP)), 3),
    }


def coverage_with(t: pd.DataFrame, scale: float) -> float:
    """Share of outcomes inside the 80% band if every sd were multiplied by `scale` (relative to t.sd)."""
    t = _dressed(t)
    t = t[t.sd > 0]
    return float((np.abs(t.actual_pir - t.model) <= Z80 * t.sd * scale).mean()) if len(t) else float("nan")


# ---------- bias ----------
def fit_bias(t: pd.DataFrame, current: dict | None = None) -> dict:
    """Multipliers per 'pos|band' from residuals of a model that already includes `current` corrections.

    ratio_r = sum(actual)/sum(model) per round; rounds weighted by BIAS_DECAY**age and by size; the segment's
    combined ratio is shrunk toward 1 by n/(n+BIAS_PRIOR_N), clipped, then composed with the current factor.
    """
    current = current or {}
    t = _dressed(t)
    t = t[t.model > 0.5]
    t["seg"] = t.fpos.astype(str) + "|" + t.min_hat.map(minutes_band)
    last = t["round"].max()
    out = {}
    for seg, g in t.groupby("seg"):
        num = den = 0.0
        for rnd, gr in g.groupby("round"):
            w = BIAS_DECAY ** (last - rnd)
            num += w * gr.actual_pir.sum()
            den += w * gr.model.sum()
        if den <= 0:
            continue
        shrink = len(g) / (len(g) + BIAS_PRIOR_N)
        ratio = 1 + shrink * (num / den - 1)
        f = float(np.clip(current.get(seg, 1.0) * ratio, *BIAS_CLIP))
        if abs(f - 1) >= 0.01:
            out[seg] = round(f, 3)
    return out


def bias_table(t: pd.DataFrame) -> pd.DataFrame:
    t = _dressed(t)
    t["seg"] = t.fpos.astype(str) + "|" + t.min_hat.map(minutes_band)
    g = t.groupby("seg").agg(n=("model", "size"), mean_err=("model", lambda s: 0.0), model=("model", "sum"), actual=("actual_pir", "sum"))
    g["mean_err"] = (t.groupby("seg").model.mean() - t.groupby("seg").actual_pir.mean()).round(2)
    g["ratio"] = (g.actual / g.model).round(3)
    return g[["n", "mean_err", "ratio"]].sort_values("n", ascending=False)


# ---------- attribution ----------
def attribution(t: pd.DataFrame) -> dict:
    """error = model - actual = (min_hat - actual_min) * rate_eff  +  actual_min * (rate_eff - actual_rate),
    with rate_eff = model / min_hat (everything that is not minutes: rate, home, pace, DvP, bias)."""
    t = _dressed(t)
    t = t[t.min_hat > 0]
    rate_eff = t.model / t.min_hat
    min_part = (t.min_hat - t.actual_min) * rate_eff
    rate_part = (t.model - t.actual_pir) - min_part
    dnp = t[(t.actual_min == 0) & (t.min_hat >= 10)]
    tot = min_part.abs().sum() + rate_part.abs().sum()
    return {
        "n": int(len(t)),
        "minutes_mae": round(float((t.min_hat - t.actual_min).abs().mean()), 2),
        "minutes_share": round(float(min_part.abs().sum() / tot), 3) if tot else None,
        "rate_share": round(float(rate_part.abs().sum() / tot), 3) if tot else None,
        "dnp_misses": int(len(dnp)),
        "dnp_cost": round(float(dnp.model.sum()), 1),
    }


def report(t: pd.DataFrame) -> str:
    c, a = calibration(t), attribution(t)
    lines = ["## Calibration (walk-forward)",
             f"- 80% band holds {c['inside_80']:.0%} of outcomes (above p90 {c['above_p90']:.0%}, below p10 {c['below_p10']:.0%}; n={c['n']}) "
             f"→ sd scale that would make it 80%: ×{c['sd_scale']}",
             "## Error attribution",
             f"- minutes MAE {a['minutes_mae']} min · share of absolute error from minutes {a['minutes_share']:.0%}, from rate {a['rate_share']:.0%}",
             f"- surprise DNPs (projected ≥10 min, played 0): {a['dnp_misses']} costing {a['dnp_cost']} projected PIR",
             "## Bias by segment (projected − actual PIR per game; ratio = actual/projected)"]
    bt = bias_table(t).head(12)
    lines += [f"- {seg}: n={int(r.n)}, err {r.mean_err:+.2f}, ratio {r.ratio}" for seg, r in bt.iterrows()]
    return "\n".join(lines)
