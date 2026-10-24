"""Defence vs Position (DvP): how much PIR each team concedes to guards / forwards / centers.

Two views per team x position, this season only:
  pir_allowed : average total PIR scored against the team by that position, per game
  piroe       : PIR over expectation - sum over opposing players of (actual PIR - that player's
                season-average PIR), per game. Removes "they just faced Vezenkov" bias.
Both are shrunk toward the league mean with weight n / (n + K) so a 7-game sample reads as a tilt.
A starters/bench split is produced as a secondary view with a stronger shrinkage.
"""
from __future__ import annotations

import pandas as pd

from elfa.config import PROCESSED

K_TEAM = 8       # games of prior weight toward league mean
K_SPLIT = 12
POS_ORDER = ["Guard", "Forward", "Center"]


def attach_positions(pg: pd.DataFrame, player_map: pd.DataFrame, market: list[dict]) -> pd.DataFrame:
    """Fantasy position (G/F/C) per official person code; falls back to the API's own position."""
    pid2pos = {str(p["id"]): (p.get("position") or {}).get("name") for p in market}
    pm = player_map.dropna(subset=["person_code"]).copy()
    pm["fpos"] = pm.platform_id.astype(str).map(pid2pos)
    code2pos = dict(zip(pm.person_code.astype(str), pm.fpos))
    pos = pg.player_code.astype(str).map(code2pos)
    api_pos = pg.position_api.replace({"Guard": "Guard", "Forward": "Forward", "Center": "Center"})
    pg = pg.copy()
    pg["fpos"] = pos.fillna(api_pos).where(lambda s: s.isin(POS_ORDER), "Forward")
    return pg


def compute_dvp(pg: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (dvp, dvp_split). Input must carry `fpos` and be a single season."""
    pg = pg[pg.played].copy()
    # player season average PIR per game (played games only)
    avg = pg.groupby("player_code").pir.mean().rename("pir_avg")
    pg = pg.join(avg, on="player_code")
    pg["pir_oe"] = pg.pir - pg.pir_avg

    def _agg(frame: pd.DataFrame, k: int, extra: list[str]) -> pd.DataFrame:
        per_game = (
            frame.groupby(["opponent", "game_code", "fpos", *extra], as_index=False)
            .agg(pir_allowed=("pir", "sum"), piroe=("pir_oe", "sum"))
        )
        team = (
            per_game.groupby(["opponent", "fpos", *extra], as_index=False)
            .agg(games=("game_code", "nunique"), pir_allowed=("pir_allowed", "mean"), piroe=("piroe", "mean"))
            .rename(columns={"opponent": "team"})
        )
        league = team.groupby(["fpos", *extra]).pir_allowed.transform("mean")
        w = team.games / (team.games + k)
        team["pir_allowed_shrunk"] = w * team.pir_allowed + (1 - w) * league
        team["piroe_shrunk"] = w * team.piroe            # league mean of PIRoE is ~0 by construction
        team["weight"] = w.round(2)
        team["league_pir_allowed"] = league
        return team

    dvp = _agg(pg, K_TEAM, [])
    dvp["rank_weak_to_strong"] = dvp.groupby("fpos").piroe_shrunk.rank(ascending=False).astype(int)
    split = _agg(pg.assign(unit=pg.starter.map({True: "starters", False: "bench"})), K_SPLIT, ["unit"])
    dvp.sort_values(["fpos", "piroe_shrunk"], ascending=[True, False]).to_csv(PROCESSED / "dvp.csv", index=False)
    split.to_csv(PROCESSED / "dvp_split.csv", index=False)
    return dvp, split


def dvp_summary(dvp: pd.DataFrame, n: int = 4) -> str:
    lines = []
    for pos in POS_ORDER:
        d = dvp[dvp.fpos == pos].sort_values("piroe_shrunk", ascending=False)
        weak = ", ".join(f"{r.team} ({r.piroe_shrunk:+.1f}, n={r.games})" for r in d.head(n).itertuples())
        strong = ", ".join(f"{r.team} ({r.piroe_shrunk:+.1f}, n={r.games})" for r in d.tail(n).itertuples())
        lines.append(f"{pos:8s} leak PIR to: {weak}")
        lines.append(f"{'':8s} stifle:      {strong}")
    return "\n".join(lines)
