"""Guarded self-recalibration, run after every pipeline refresh.

1. Minutes sub-model: grid over minutes weights / DNP penalty / small-sample prior, scored on minutes MAE.
2. Rate sub-model:    grid over recent-form weight / rate prior / DvP / home effect, scored on PIR MAE
                      (with the chosen minutes params).
3. Bias layer:        shrunk segment multipliers fitted on the training rounds' residuals.
4. Calibration:       sd scale so the 80% band holds 80% on the training rounds.
Gate: candidates are compared with the current params on the last 2 played rounds (never seen in fitting).
A candidate is adopted only if it wins on EVERY hold-out round and by >= MIN_GAIN on average; otherwise the
best one is kept as a shadow challenger and promoted if it then wins PROMOTE_STREAK newest rounds in a row.
The sd scale has its own gate (hold-out coverage closer to 80%).
Also writes model_health.json (drift flag, calibration, attribution) for the report and the app.
"""
from __future__ import annotations

import dataclasses
import datetime as dt
import json

import numpy as np
import pandas as pd

from elfa.config import PROCESSED
from elfa.model.backtest import backtest
from elfa.model.calibrate import attribution, calibration, coverage_with, fit_bias, report
from elfa.model.projection import Params, _player_form

MIN_GAIN = 0.03
PROMOTE_STREAK = 3
MINUTES_GRID = {
    "w_minutes": [(0.5, 0.3, 0.2), (0.3, 0.4, 0.3), (0.2, 0.3, 0.5), (0.1, 0.3, 0.6), (0.0, 0.5, 0.5)],
    "dnp_recent_penalty": [0.3, 0.5, 0.8],
    "minutes_sample_prior": [0.5, 1.5, 3.0],
}
RATE_GRID = {
    "lam_recent": [0.3, 0.6, 0.8],
    "rate_prior_minutes": [20.0, 40.0, 80.0],
    "gamma_dvp": [0.0, 0.6, 1.0],
    "eta_home": [0.02, 0.06],
}
SUBSET = "projected >= 15 min"


def _replace(p: Params, **kw) -> Params:
    return dataclasses.replace(p, **kw)


def minutes_mae(pg: pd.DataFrame, rounds: list[int], p: Params) -> float:
    errs = []
    for r in rounds:
        train, test = pg[pg["round"] < r], pg[pg["round"] == r]
        played = train[train.played]
        if played.empty or test.empty:
            continue
        rate = played.pir.sum() / played.minutes.sum()
        f = _player_form(train, rate, played.pir.std(), p).set_index("person_code")
        m = test.merge(f[["min_hat"]], left_on="player_code", right_index=True)
        m = m[(m.minutes > 0) | (m.min_hat >= 5)]
        errs.append((m.min_hat - m.minutes).abs())
    return float(pd.concat(errs).mean()) if errs else float("inf")


def round_mae(pg, schedule, rounds, p) -> dict[int, float]:
    t = backtest(pg, schedule, rounds, p).table
    t = t[t.min_hat >= 15]
    return {int(r): float((g.model - g.actual_pir).abs().mean()) for r, g in t.groupby("round")}


def _grid_minutes(pg, train, base: Params) -> Params:
    best, best_v = base, minutes_mae(pg, train, base)
    for w in MINUTES_GRID["w_minutes"]:
        for d in MINUTES_GRID["dnp_recent_penalty"]:
            for s in MINUTES_GRID["minutes_sample_prior"]:
                p = _replace(base, w_minutes=w, dnp_recent_penalty=d, minutes_sample_prior=s)
                v = minutes_mae(pg, train, p)
                if v < best_v - 1e-9:
                    best, best_v = p, v
    return best


def _grid_rate(pg, schedule, train, base: Params) -> Params:
    def mae(p):
        m = round_mae(pg, schedule, train, p)
        return float(np.mean(list(m.values()))) if m else float("inf")
    best, best_v = base, mae(base)
    for lam in RATE_GRID["lam_recent"]:
        for rp in RATE_GRID["rate_prior_minutes"]:
            for g in RATE_GRID["gamma_dvp"]:
                for eta in RATE_GRID["eta_home"]:
                    p = _replace(base, lam_recent=lam, rate_prior_minutes=rp, gamma_dvp=g, eta_home=eta)
                    v = mae(p)
                    if v < best_v - 1e-9:
                        best, best_v = p, v
    return best


def _key(p: Params) -> str:
    d = dataclasses.asdict(p)
    d.pop("flags", None)
    return json.dumps(d, sort_keys=True, default=str)


def _load_json(name: str, default):
    fp = PROCESSED / name
    try:
        return json.loads(fp.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _params_from(d: dict) -> Params:
    d = {k: (tuple(v) if isinstance(v, list) else v) for k, v in d.items() if k in Params.__dataclass_fields__}
    return Params(**d)


def drift_check(pg, schedule, rounds, p: Params) -> dict:
    t = backtest(pg, schedule, rounds, p).table
    t15 = t[t.min_hat >= 15]
    per = []
    for r, g in t15.groupby("round"):
        model = float((g.model - g.actual_pir).abs().mean())
        base = min(float((g.base_mean - g.actual_pir).abs().mean()), float((g.base_last3 - g.actual_pir).abs().mean()))
        per.append({"round": int(r), "mae_model": round(model, 2), "mae_best_baseline": round(base, 2), "model_wins": model < base})
    reasons = []
    if len(per) >= 2 and not per[-1]["model_wins"] and not per[-2]["model_wins"]:
        reasons.append(f"model lost to a naive baseline in R{per[-2]['round']} and R{per[-1]['round']}")
    sc = PROCESSED / "scorecard.csv"
    if sc.exists():
        s = pd.read_csv(sc).sort_values("matchday")
        if len(s) >= 2 and (s.z.tail(2).abs() > 2).all():
            reasons.append(f"team total off by >2 sd in MD {int(s.matchday.iloc[-2])} and MD {int(s.matchday.iloc[-1])}")
    cal = calibration(t)
    if abs(cal["inside_80"] - 0.8) > 0.1:
        reasons.append(f"80% band holds {cal['inside_80']:.0%} - uncertainty mis-calibrated")
    return {"drift": bool(reasons), "reasons": reasons, "per_round": per, "calibration": cal,
            "attribution": attribution(t), "table": t}


def learn(pg: pd.DataFrame, schedule: list[dict], rounds: list[int]) -> str:
    if len(rounds) < 3:
        return "learn: need at least 3 played rounds"
    n_hold = 2 if len(rounds) >= 4 else 1
    train, hold = rounds[:-n_hold], rounds[-n_hold:]
    current = Params.load()
    out = [f"learn: train R{train[0]}-R{train[-1]}, hold-out R{', R'.join(map(str, hold))}"]

    # 1-2: core sub-models (fitted without the bias/sd layers)
    core0 = _replace(current, bias={}, sd_scale=1.0)
    core = _grid_rate(pg, schedule, train, _grid_minutes(pg, train, core0))
    # 3: bias on the training residuals, for both the current core and the new core
    def with_bias(p):
        return _replace(p, bias=fit_bias(backtest(pg, schedule, train, p).table))
    cands = {"new core + bias": with_bias(core), "new core": core, "current core + new bias": with_bias(core0)}

    cur_mae = round_mae(pg, schedule, hold, current)
    best_name, best_p, best_gain = None, None, -np.inf
    for name, p in cands.items():
        m = round_mae(pg, schedule, hold, _replace(p, sd_scale=current.sd_scale))
        diffs = [cur_mae[r] - m[r] for r in hold if r in m and r in cur_mae]
        gain = float(np.mean(diffs)) if diffs else -np.inf
        consistent = bool(diffs) and all(d > 0 for d in diffs)
        out.append(f"- {name}: hold-out MAE " + ", ".join(f"R{r} {m.get(r, float('nan')):.2f}" for r in hold)
                   + f" vs current " + ", ".join(f"{cur_mae.get(r, float('nan')):.2f}" for r in hold) + f" (gain {gain:+.2f}{', every round' if consistent else ''})")
        if consistent and gain > best_gain:
            best_name, best_p, best_gain = name, p, gain
    adopted = current
    if best_p is not None and best_gain >= MIN_GAIN:
        adopted = _replace(best_p, sd_scale=current.sd_scale)
        out.append(f"→ ADOPTED '{best_name}' (gain {best_gain:+.2f} on every hold-out round)")
    else:
        out.append("→ kept current core")

    # shadow challenger: the strongest non-adopted candidate, tracked on the newest round
    newest = rounds[-1]
    ch = _load_json("challenger.json", {})
    log = pd.DataFrame(_load_json("learn_log.json", []))
    if adopted is current:
        if ch.get("params"):
            chp = _params_from(ch["params"])
            m_ch = round_mae(pg, schedule, [newest], chp).get(newest)
            m_cu = cur_mae.get(newest) if newest in cur_mae else round_mae(pg, schedule, [newest], current).get(newest)
            if m_ch is not None and m_cu is not None and not ((not log.empty) and ((log["round"] == newest) & (log.challenger == ch["id"])).any()):
                log = pd.concat([log, pd.DataFrame([{"round": newest, "challenger": ch["id"], "mae_champion": round(m_cu, 3),
                                                       "mae_challenger": round(m_ch, 3), "challenger_wins": m_ch < m_cu}])], ignore_index=True)
            mine = log[log.challenger == ch["id"]].sort_values("round") if not log.empty else log
            if len(mine) >= PROMOTE_STREAK and mine.challenger_wins.tail(PROMOTE_STREAK).all():
                adopted = _replace(chp, sd_scale=current.sd_scale)
                out.append(f"→ PROMOTED shadow challenger {ch['id']} (won {PROMOTE_STREAK} newest rounds in a row)")
                ch = {}
            elif len(mine) >= 2 and not mine.challenger_wins.tail(2).any():
                ch = {}  # lost twice running - retire it
        if not ch and best_name is not None and adopted is current:
            p = cands[best_name]
            ch = {"id": dt.datetime.now(dt.UTC).strftime("%Y%m%d%H%M"), "since_round": newest, "name": best_name,
                  "params": dataclasses.asdict(p)}
        elif not ch and adopted is current:
            p = cands["new core + bias"]
            if _key(p) != _key(_replace(current, sd_scale=1.0)):
                ch = {"id": dt.datetime.now(dt.UTC).strftime("%Y%m%d%H%M"), "since_round": newest, "name": "new core + bias",
                      "params": dataclasses.asdict(p)}
        if ch:
            out.append(f"- shadow challenger {ch['id']} ('{ch['name']}', since R{ch['since_round']}) - would be promoted after {PROMOTE_STREAK} straight newest-round wins")
    (PROCESSED / "challenger.json").write_text(json.dumps(ch, indent=1, default=str), encoding="utf-8")
    (PROCESSED / "learn_log.json").write_text(log.to_json(orient="records", indent=1) if not log.empty else "[]", encoding="utf-8")

    # 4: sd calibration, own gate: fit k on train, keep it only if hold-out coverage gets closer to 80%
    t_train = backtest(pg, schedule, train, _replace(adopted, sd_scale=1.0)).table
    k = calibration(t_train)["sd_scale"]
    t_hold = backtest(pg, schedule, hold, _replace(adopted, sd_scale=1.0)).table
    cov_cur, cov_new = coverage_with(t_hold, adopted.sd_scale), coverage_with(t_hold, k)
    if abs(cov_new - 0.8) + 0.01 < abs(cov_cur - 0.8):
        out.append(f"→ sd scale {adopted.sd_scale} → {k} (hold-out 80% band {cov_cur:.0%} → {cov_new:.0%})")
        adopted = _replace(adopted, sd_scale=k)
    else:
        out.append(f"- sd scale kept at {adopted.sd_scale} (hold-out 80% band {cov_cur:.0%}; candidate ×{k} → {cov_new:.0%})")

    if _key(adopted) != _key(current):
        adopted.save(note=f"{dt.date.today()}: {'; '.join(o[2:] for o in out if o.startswith('→') and 'kept' not in o)}")

    # health: drift + calibration + attribution with the params now in force
    h = drift_check(pg, schedule, rounds, adopted)
    t = h.pop("table")
    health = {"generated_utc": dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"), **h,
              "params": {k_: v for k_, v in dataclasses.asdict(adopted).items() if k_ != "flags"},
              "challenger": ch or None}
    (PROCESSED / "model_health.json").write_text(json.dumps(health, indent=1, default=str), encoding="utf-8")
    (PROCESSED / "model_health.md").write_text("# Model health\n\n" + ("**DRIFT:** " + "; ".join(h["reasons"]) if h["drift"] else "No drift flags.")
                                              + "\n\n" + "\n".join(out) + "\n\n" + report(t), encoding="utf-8")
    out.append(("DRIFT: " + "; ".join(h["reasons"])) if h["drift"] else "health: no drift flags")
    return "\n".join(out)
