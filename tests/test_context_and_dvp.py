"""Team context / usage / FDR sanity, and the DvP position-attribution check."""
import json

import pandas as pd
import pytest

from elfa.config import PROCESSED, RAW
from elfa.features.boxscores import build_player_games
from elfa.features.context import fixture_fdr, team_context, usage
from elfa.features.dvp import POS_ORDER, attach_positions
from elfa.model.teams import team_ratings


@pytest.fixture(scope="module")
def pg():
    df = build_player_games(["E2026"])
    market = json.loads((RAW / "fantaking" / "md_08" / "market.json").read_text(encoding="utf-8"))
    pm = pd.read_csv(PROCESSED / "player_map.csv", dtype={"platform_id": str, "person_code": str})
    return attach_positions(df[df.season == "E2026"], pm, market)


@pytest.fixture(scope="module")
def schedule():
    return json.loads((RAW / "euroleague" / "E2026" / "games.json").read_text(encoding="utf-8"))


def test_team_context_shape_and_ranges(pg):
    ctx = team_context(pg)
    assert len(ctx) == 20 and ctx.team.is_unique
    assert ctx.fdr.between(1, 5).all() and ctx.matchup_ease.between(0, 100).all()
    assert ctx.pace.between(60, 95).all()
    # allowed == what opponents produced: league totals must balance
    assert abs(ctx.pts.sum() - ctx.pts_allowed.sum()) < 0.1   # values are rounded to 3 dp
    assert abs(ctx.pir.sum() - ctx.pir_allowed.sum()) < 0.1


def test_usage_ranges(pg):
    u = usage(pg)
    assert u.shot_share.dropna().between(0, 60).all()
    assert u.fga_per_min.between(0, 2).all()
    assert set(u.role_signal.fillna("").unique()) <= {"", "rising", "falling"}


def test_fdr_next_five(pg, schedule):
    ctx = team_context(pg)
    f = fixture_fdr(schedule, ctx, team_ratings(pg, schedule), {}, from_round=8, n_games=5)
    assert f.team.nunique() == 20 and f.groupby("team").size().max() == 5
    assert f.fdr.between(1, 5).all()
    assert (f.groupby("game_code").win_prob.sum().round(6) == 1).all()


def test_dvp_position_attribution(pg):
    """Every played player-game carries a G/F/C, and the platform (not the API fallback) supplies it for almost all."""
    played = pg[pg.played]
    assert played.fpos.isin(POS_ORDER).all()
    pm = pd.read_csv(PROCESSED / "player_map.csv", dtype={"platform_id": str, "person_code": str}).dropna(subset=["person_code"])
    platform_coverage = played.player_code.astype(str).isin(set(pm.person_code.astype(str))).mean()
    assert platform_coverage >= 0.9, f"only {platform_coverage:.0%} of player-games have a platform position"
    # per game, positions sum to the team total PIR (nothing dropped by the attribution)
    by_pos = played.groupby(["game_code", "team", "fpos"]).pir.sum().groupby(["game_code", "team"]).sum()
    total = played.groupby(["game_code", "team"]).pir.sum()
    assert (by_pos - total).abs().max() < 1e-9
