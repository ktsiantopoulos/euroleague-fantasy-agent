"""Availability flags in the report and the season-start price-band correction layer."""
import pandas as pd

import elfa.report.recommend as rec
from elfa.model.calibrate import fit_tier_bias
from elfa.model.projection import Params, availability_flag, price_band, price_tier, tier_factor


def test_availability_flag():
    assert availability_flag(True, 0.0) == "OUT (injured)"
    assert availability_flag(False, 0.0) == "OUT (0% to play)"
    assert availability_flag(True, 0.25) == "injured, 25% to play"
    assert availability_flag(False, 0.5) == "doubtful, 50% to play"
    assert availability_flag(False, 1.0) is None


def test_injured_squad_player_reaches_flags_section():
    proj = pd.DataFrame({"name": ["Hayes", "Fit Guy", "Coach"], "in_roster": [True, True, True],
                         "flags": ["OUT (injured)", "", "coach"]})
    assert rec._flags_section(proj) == "- Hayes: OUT (injured)"


def test_price_tier_and_band():
    assert price_tier(5.3) == "<=6" and price_tier(6.0) == "<=6" and price_tier(6.1) == "6-9"
    assert price_tier(13.0) == "9-13" and price_tier(18.9) == "13+"
    assert price_tier(None) is None and price_tier(float("nan")) is None
    assert price_band(5.0) == "cheap" and price_band(10.0) == "mid" and price_band(15.0) == "premium"


def test_tier_factor_defaults_to_one():
    p = Params(tier_bias={"cheap": 0.8, "premium": 1.1})
    assert tier_factor(p, "Guard", 5.0) == 0.8 and tier_factor(p, "Center", 16.0) == 1.1
    assert tier_factor(p, "Guard", 8.0) == 1.0 and tier_factor(p, "Guard", None) == 1.0
    assert tier_factor(Params(), "Guard", 5.0) == 1.0


def test_fit_tier_bias_direction_and_shrinkage():
    rows = []
    for rnd in (5, 6, 7):
        rows += [{"round": rnd, "model": 10.0, "actual_pir": 7.0, "actual_min": 15, "min_hat": 15, "price0": 5.0}] * 40
        rows += [{"round": rnd, "model": 10.0, "actual_pir": 12.0, "actual_min": 28, "min_hat": 28, "price0": 15.0}] * 40
        rows += [{"round": rnd, "model": 10.0, "actual_pir": 10.0, "actual_min": 20, "min_hat": 20, "price0": 8.0}] * 40
    f = fit_tier_bias(pd.DataFrame(rows))
    assert 0.75 <= f["cheap"] < 0.8          # raw 0.70, shrunk toward 1 and clipped at 0.75
    assert 1.15 < f["premium"] < 1.2         # raw 1.20 shrunk by n/(n+30)
    assert "mid" not in f                    # no bias -> no entry
