"""Lock-time freeze, decision scorecard maths, and the calibration / bias / attribution layers."""
import datetime as dt
import json
from types import SimpleNamespace

import numpy as np
import pandas as pd

import elfa.report.recommend as rec
from elfa.model.calibrate import attribution, calibration, fit_bias
from elfa.model.projection import Params, bias_factor, minutes_band
from elfa.model.scorecard import hindsight_best, score, squad_sd

# ---------- freeze at lock ----------
G = SimpleNamespace
FIRST = [G(round=9, date_utc="2026-10-29T19:00:00Z"), G(round=9, date_utc="2026-10-30T16:00:00Z")]


def _sol(ids):
    sq = pd.DataFrame({"platform_id": ids, "name": ids, "pos": "Guard", "role": "starter", "captain": [i == ids[0] for i in ids],
                       "md_pts": 10.0, "md_sd": 4.0})
    return SimpleNamespace(squad=sq, expected_md_pts=50.0, captain=ids[0], trades_out=[], trades_in=[])


def _freeze(tmp_path, monkeypatch, now, first=FIRST, open_=True):
    monkeypatch.setattr(rec, "PROCESSED", tmp_path)
    base = SimpleNamespace(open=open_, ids={"1", "2"})
    proj = pd.DataFrame({"platform_id": ["1", "2"], "md_pts": [10, 12]})
    return rec.freeze_if_pre_lock(9, proj, first, base, _sol(["1"]), _sol(["2"]), 107.3, 4, now=now, params=Params())


def test_freezes_before_lock(tmp_path, monkeypatch):
    msg = _freeze(tmp_path, monkeypatch, dt.datetime(2026, 10, 29, 10, tzinfo=dt.UTC))
    assert msg.startswith("written")
    d = json.loads((tmp_path / "decision_md09_locked.json").read_text())
    assert d["lock_utc"] == "2026-10-29T18:59:00Z" and d["trades_left"] == 4
    assert (tmp_path / "projection_md09_locked.csv").exists()


def test_never_overwrites_after_lock(tmp_path, monkeypatch):
    msg = _freeze(tmp_path, monkeypatch, dt.datetime(2026, 10, 29, 20, tzinfo=dt.UTC))
    assert msg.startswith("kept") and not (tmp_path / "projection_md09_locked.csv").exists()


def test_skips_stale_pull_with_next_rounds_fixtures(tmp_path, monkeypatch):
    stale = [G(round=10, date_utc="2026-11-04T19:45:00Z")]
    msg = _freeze(tmp_path, monkeypatch, dt.datetime(2026, 10, 29, 10, tzinfo=dt.UTC), first=stale)
    assert msg.startswith("skipped") and not list(tmp_path.iterdir())


# ---------- scorecard ----------
def test_score_matches_platform_weights():
    # MD 8 as played: total 155.15 on the platform
    sq = [("D", "starter", 0, 16), ("S", "starter", 0, 13), ("V", "starter", 1, 20.9), ("N", "starter", 0, 6.6),
          ("M", "starter", 0, 17.6), ("W", "sixth", 0, 17), ("Ne", "bench", 0, 23.1), ("F", "bench", 0, 9.9),
          ("U", "bench", 0, 0), ("P", "bench", 0, 3.3), ("C", "coach", 0, 25)]
    squad = [{"platform_id": n, "role": r, "captain": bool(c)} for n, r, c, _ in sq]
    assert score(squad, {n: p for n, _, _, p in sq}) == 155.15
    assert round(squad_sd([{"platform_id": "a", "role": "bench", "captain": False},
                           {"platform_id": "b", "role": "starter", "captain": True}], {"a": 4, "b": 3}), 3) == round(np.sqrt(4 + 36), 3)


def test_hindsight_respects_trade_limit():
    rows = []
    for pos, n in (("Guard", 6), ("Forward", 6), ("Center", 4), ("Head Coach", 2)):
        rows += [{"platform_id": f"{pos[0]}{i}", "pos": pos, "team": f"T{i}", "quotation": 5.0} for i in range(n)]
    proj = pd.DataFrame(rows)
    pts = {r["platform_id"]: (30.0 if r["platform_id"].endswith(("4", "5")) else 5.0) for r in rows}
    base = {f"G{i}" for i in range(4)} | {f"F{i}" for i in range(4)} | {"C0", "C1", "H0"}
    v0, sq0 = hindsight_best(proj, pts, 100.0, base, 0)
    v2, sq2 = hindsight_best(proj, pts, 100.0, base, 2)
    assert {p["platform_id"] for p in sq0} == base
    assert len({p["platform_id"] for p in sq2} - base) == 2 and v2 > v0


# ---------- calibration / bias / attribution ----------
def _table(rng, n=600, bias=1.0, sd_true=6.0, sd_model=4.0):
    min_hat = rng.uniform(12, 28, n)
    model = min_hat * 0.6
    actual_min = np.clip(min_hat + rng.normal(0, 3, n), 0, 40)
    actual = model * bias + rng.normal(0, sd_true, n)
    return pd.DataFrame({"round": rng.integers(4, 9, n), "fpos": "Guard", "min_hat": min_hat, "model": model, "sd": sd_model,
                         "actual_pir": actual, "actual_min": actual_min})


def test_calibration_widens_narrow_bands():
    c = calibration(_table(np.random.default_rng(0)))
    assert c["inside_80"] < 0.75 and c["sd_scale"] > 1.3


def test_bias_is_shrunk_and_clipped():
    b = fit_bias(_table(np.random.default_rng(1), bias=1.3))
    assert b and all(1.15 < v < 1.4 for v in b.values())         # near the true 1.3, after shrinkage and noise
    assert all(1.0 < v <= 1.6 for v in fit_bias(_table(np.random.default_rng(4), n=4000, bias=3.0)).values())
    assert all(int(k.split("|")[1].split("-")[0].lstrip("<")) < 20 for k in b)   # nothing fitted at 20+ min
    # null case: no true bias -> only noise-sized factors (prior N=30 trades a wider noise floor for speed;
    # the hold-out gate in learning.bias_gate is what keeps a noise-only layer out)
    assert all(abs(v - 1) < 0.08 for v in fit_bias(_table(np.random.default_rng(2), bias=1.0)).values())


def test_bias_factor_lookup():
    p = Params(bias={"Guard|15-20": 1.1})
    assert minutes_band(15) == "15-20" and minutes_band(12) == "10-15" and minutes_band(9.9) == "<10"
    assert bias_factor(p, "Guard", 15) == 1.1 and bias_factor(p, "Center", 15) == 1.0 and bias_factor(p, "Guard", 25) == 1.0


def test_bias_skips_starter_minutes():
    t = _table(np.random.default_rng(5), bias=1.4)
    t["min_hat"] = t.min_hat + 10          # every player projected 22-38 min
    assert fit_bias(t) == {}


def test_attribution_shares_sum_to_one():
    a = attribution(_table(np.random.default_rng(3)))
    assert abs(a["minutes_share"] + a["rate_share"] - 1) < 1e-6 and a["minutes_mae"] > 0


def test_bias_gate_adopts_real_bias_and_rejects_noise(monkeypatch):
    import elfa.model.learning as L

    def fake_backtest(true_bias):
        def bt(pg, schedule, rounds, p):
            rng = np.random.default_rng(sum(rounds) * 7)
            t = _table(rng, n=900, bias=true_bias)
            t["min_hat"] = rng.uniform(4, 19, len(t))
            t["model"] = t.min_hat * 0.6
            t["actual_pir"] = t.model * true_bias + rng.normal(0, 6, len(t))
            t["round"] = rng.choice(rounds, len(t))
            t["model"] = t.model * t.fpos.astype(str).str.cat(t.min_hat.map(minutes_band), sep="|").map(p.bias or {}).fillna(1.0)
            return SimpleNamespace(table=t)
        return bt

    monkeypatch.setattr(L, "backtest", fake_backtest(1.4))
    p, msg = L.bias_gate(None, None, [4, 5, 6, 7], [8, 9], Params())
    assert p.bias and msg.startswith("→ ADOPTED")
    monkeypatch.setattr(L, "backtest", fake_backtest(1.0))
    p, msg = L.bias_gate(None, None, [4, 5, 6, 7], [8, 9], Params())
    assert p.bias == {} and "ADOPTED" not in msg
