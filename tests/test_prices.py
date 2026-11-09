"""Price-dynamics model and the market term in the optimiser."""
import pandas as pd

from elfa.model import prices as P
from elfa.optimise.lineup import optimise
from tests.test_optimiser import _market


def test_expected_price_change_follows_excess_and_skips_coaches_and_byes():
    proj = pd.DataFrame([
        {"platform_id": "a", "pos": "Guard", "md_pts": 20.0, "avg_pts_platform": 10.0, "games_md": 1},   # +10 excess
        {"platform_id": "b", "pos": "Guard", "md_pts": 0.0, "avg_pts_platform": 20.0, "games_md": 1},    # injured: -20
        {"platform_id": "c", "pos": "Guard", "md_pts": 0.0, "avg_pts_platform": 12.0, "games_md": 0},    # no game: no move
        {"platform_id": "h", "pos": "Head Coach", "md_pts": 15.0, "avg_pts_platform": 5.0, "games_md": 1},
    ])
    model = {"slope": 0.03, "intercept": 0.0, "fitted": True}
    out = P.expected_price_change(proj, model, horizon_mds=3, decay=0.9)
    mult = 1 + 0.9 + 0.81
    assert abs(out["a"] - 0.3 * mult) < 1e-6
    assert abs(out["b"] + 0.6 * mult) < 1e-6
    assert out["c"] == 0.0 and out["h"] == 0.0


def test_fit_falls_back_to_default_slope_on_thin_log(tmp_path, monkeypatch):
    monkeypatch.setattr(P, "PRICES", tmp_path)
    monkeypatch.setattr(P, "MODEL_FP", tmp_path / "price_model.json")
    m = P.fit_price_model(write=True)
    assert m["slope"] == P.DEFAULT_SLOPE and not m["fitted"]
    assert (tmp_path / "price_model.json").exists()


def test_market_term_shifts_the_squad_toward_rising_players():
    df = _market()
    cheap = df.sort_values("quotation")
    prev = set(cheap[cheap.pos == "Guard"].platform_id.head(4)) | set(cheap[cheap.pos == "Forward"].platform_id.head(4)) \
        | set(cheap[cheap.pos == "Center"].platform_id.head(2)) | set(cheap[cheap.pos == "Head Coach"].platform_id.head(1))
    base = optimise(df, budget=100.0, prev_ids=prev, max_trades=4, mu_price=0.0)
    chosen = set(base.squad.platform_id)
    # a guard just outside the squad is expected to rise sharply; everyone in the squad is flat
    outsider = next(i for i in df[df.pos == "Guard"].sort_values("md_pts", ascending=False).platform_id if i not in chosen)
    epc = {outsider: 3.0}
    sol = optimise(df, budget=100.0, prev_ids=prev, max_trades=4, mu_price=10.0, exp_price_change=epc)
    assert sol.status.startswith("Optimal")
    assert outsider in set(sol.squad.platform_id)
    assert sol.price_gain == 3.0 and sol.price_value == 30.0
    assert base.price_gain == 0.0 and base.price_value == 0.0
