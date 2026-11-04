"""Optimiser feasibility and rule compliance on a synthetic market."""
import random

import pandas as pd

from elfa.optimise.lineup import optimise


def _market(seed=1):
    random.seed(seed)
    rows = []
    teams = [f"T{i}" for i in range(10)]
    i = 0
    for pos, n in (("Guard", 40), ("Forward", 40), ("Center", 20), ("Head Coach", 10)):
        for _ in range(n):
            i += 1
            q = round(random.uniform(4, 18), 1) if pos != "Head Coach" else round(random.uniform(4, 8), 1)
            md = round(q * random.uniform(0.6, 1.6), 1) if pos != "Head Coach" else round(random.uniform(-5, 15), 1)
            rows.append({"platform_id": str(i), "name": f"P{i}", "pos": pos, "team": teams[i % 10], "quotation": q,
                         "md_pts": md, "md_sd": 6.0, "horizon_pts": md * 1.5, "games_md": 1,
                         "first_turn": 1 + (i % 2), "games_json": "[]"})
    return pd.DataFrame(rows)


def test_optimiser_respects_rules():
    df = _market()
    cheap = df.sort_values("quotation")
    prev = set(cheap[cheap.pos == "Guard"].platform_id.head(4)) | set(cheap[cheap.pos == "Forward"].platform_id.head(4)) \
        | set(cheap[cheap.pos == "Center"].platform_id.head(2)) | set(cheap[cheap.pos == "Head Coach"].platform_id.head(1))
    sol = optimise(df, budget=100.0, prev_ids=prev, max_trades=4)
    sq = sol.squad
    assert sol.status == "Optimal"
    assert len(sq) == 11 and sq.quotation.sum() <= 100.0 + 1e-6
    assert sq.pos.value_counts().to_dict() == {"Guard": 4, "Forward": 4, "Center": 2, "Head Coach": 1}
    assert sq.role.value_counts().to_dict() == {"starter": 5, "sixth": 1, "bench": 4, "coach": 1}
    assert sq.captain.sum() == 1 and sq[sq.captain].role.iloc[0] == "starter"
    assert sq[sq.role == "sixth"].pos.iloc[0] != "Center"
    assert (sq[(sq.role == "bench") & (sq.first_turn >= 2)].shape[0]) >= 2
    assert sq.team.value_counts().max() <= 6
    assert len(sol.trades_in) <= 4
    hold = optimise(df, budget=100.0, prev_ids=prev, max_trades=4, lock_squad=True)
    assert set(hold.squad.platform_id) == prev
    assert sol.expected_md_pts >= hold.expected_md_pts


def _prev(df):
    cheap = df.sort_values("quotation")
    return set(cheap[cheap.pos == "Guard"].platform_id.head(4)) | set(cheap[cheap.pos == "Forward"].platform_id.head(4)) \
        | set(cheap[cheap.pos == "Center"].platform_id.head(2)) | set(cheap[cheap.pos == "Head Coach"].platform_id.head(1))


def test_availability_gate_blocks_thin_sample_trade_ins():
    df = _market()
    df["n_games"] = 9
    df["prob_play"] = 1.0
    prev = _prev(df)
    star = df[(df.pos == "Guard") & ~df.platform_id.isin(prev)].platform_id.iloc[0]
    df.loc[df.platform_id == star, ["md_pts", "horizon_pts", "quotation"]] = [60.0, 90.0, 5.0]
    assert star in set(optimise(df, 100.0, prev, 4).squad.platform_id)
    df.loc[df.platform_id == star, "n_games"] = 1
    assert star not in set(optimise(df, 100.0, prev, 4).squad.platform_id)
    df.loc[df.platform_id == star, ["n_games", "prob_play"]] = [9, 0.4]
    assert star not in set(optimise(df, 100.0, prev, 4).squad.platform_id)
    # an owned player is never forced out by the gate
    df.loc[df.platform_id == star, "prob_play"] = 1.0
    prev2 = (prev - {sorted(p for p in prev if df.set_index("platform_id").pos[p] == "Guard")[0]}) | {star}
    df.loc[df.platform_id == star, "n_games"] = 1
    assert star in set(optimise(df, 100.0, prev2, 4).squad.platform_id)


def test_trade_hurdle_reduces_trades_and_parses_games_from_why():
    df = _market()
    df["why"] = "20 min proj (starter, last 20), 0.60 PIR/min over 7 g · T1"
    prev = _prev(df)
    free = optimise(df, 100.0, prev, 4, trade_hurdle=0.0, min_games_in=3)
    strict = optimise(df, 100.0, prev, 4, trade_hurdle=100.0, min_games_in=3)
    # the synthetic baseline may need one trade to satisfy the night-balance rule, so compare counts
    assert len(strict.trades_in) < len(free.trades_in)
    assert free.trade_penalty == 0.0 and strict.trade_penalty == 100.0 * len(strict.trades_in)
    taxed = optimise(df, 100.0, prev, 4, trade_hurdle=1.0, min_games_in=3)
    assert taxed.trade_penalty == len(taxed.trades_in) * 1.0
    df["why"] = "over 2 g"
    gated = optimise(df, 100.0, prev, 4, min_games_in=3)
    pos = dict(zip(df.name, df.pos))
    assert all(pos[n] == "Head Coach" for n in gated.trades_in)  # only coaches (exempt) are buyable
