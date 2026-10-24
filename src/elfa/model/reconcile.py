"""Phase 0 gate: platform fantasy points must equal official PIR for every player-game.

Uses the per-player `fantasy-pts` history pulled with `elfa pull-platform --history`,
joins each record to the official game by (home club, date) and to the player by the
player map, and reports mismatches.
"""
from __future__ import annotations

import json

import pandas as pd

from elfa.config import PROCESSED, RAW

WIN_BONUS = 0.10


def fantasy_points(pir: float, team_won: bool) -> float:
    """Platform scoring as verified on matchdays 1-7: PIR, plus 10% of |PIR| when the team wins."""
    return round(pir + (WIN_BONUS * abs(pir) if team_won else 0.0), 1)


def reconcile() -> pd.DataFrame:
    pg = pd.read_parquet(PROCESSED / "player_games.parquet")
    pg = pg[pg.season == pg.season.max()]
    tm = pd.read_csv(PROCESSED / "team_map.csv")
    pm = pd.read_csv(PROCESSED / "player_map.csv", dtype={"platform_id": str, "person_code": str})
    t2o = dict(zip(tm.platform_abbr, tm.official_code))
    p2o = dict(zip(pm.platform_id, pm.person_code))

    season = pg.season.max()
    sched = json.loads((RAW / "euroleague" / season / "games.json").read_text(encoding="utf-8"))
    winner = {}
    for g in sched:
        if g.get("played"):
            ls, rs = g["local"]["score"], g["road"]["score"]
            winner[g["gameCode"]] = g["local"]["club"]["code"] if ls > rs else g["road"]["club"]["code"]
    games = pg[["game_code", "team", "home", "date_utc"]].drop_duplicates()
    home_games = games[games.home].assign(day=lambda d: d.date_utc.dt.date)
    key_to_game = {(r.team, r.day): r.game_code for r in home_games.itertuples()}
    pir_lookup = {(r.game_code, r.player_code): (r.pir, r.minutes, winner.get(r.game_code) == r.team)
                  for r in pg.itertuples()}

    rows = []
    for fp in sorted((RAW / "fantaking" / "fantasy_pts").glob("*.json")):
        pid, md = fp.stem.split("_md")
        j = json.loads(fp.read_text(encoding="utf-8"))
        if "error" in j or not j.get("match"):
            continue
        m = j["match"]
        home_off = t2o.get(m["home_team"]["abbreviation"])
        day = pd.Timestamp(m["started_at"]).date()
        game_code = key_to_game.get((home_off, day))
        person = p2o.get(pid)
        official = pir_lookup.get((game_code, person)) if game_code and isinstance(person, str) else None
        expected = fantasy_points(official[0], official[2]) if official else None
        rows.append(
            {
                "platform_id": pid, "matchday": int(md), "person_code": person, "game_code": game_code,
                "platform_pts": j.get("fantasy_pts"),
                "official_pir": official[0] if official else None,
                "official_min": official[1] if official else None,
                "team_won": official[2] if official else None,
                "expected_pts": expected,
                "status": (
                    "no_game" if not game_code else "no_player" if not isinstance(person, str)
                    else "no_boxscore_row" if official is None
                    else "ok" if abs(expected - (j.get("fantasy_pts") or 0)) < 0.05 else "MISMATCH"
                ),
            }
        )
    df = pd.DataFrame(rows, columns=["platform_id", "matchday", "person_code", "game_code", "platform_pts",
                                     "official_pir", "official_min", "team_won", "expected_pts", "status"])
    df.to_csv(PROCESSED / "reconcile.csv", index=False)
    return df


def gate_report(df: pd.DataFrame) -> str:
    if df.empty:
        return "no fantasy-pts history found - run `elfa pull-platform --history` first"
    counts = df.status.value_counts().to_dict()
    total = len(df)
    ok = counts.get("ok", 0)
    lines = [f"player-games compared: {total}", f"exact matches: {ok} ({ok / max(total, 1):.1%})"]
    for k, v in counts.items():
        if k != "ok":
            lines.append(f"  {k}: {v}")
    mm = df[df.status == "MISMATCH"].head(15)
    if len(mm):
        lines.append("\nfirst mismatches:")
        lines.append(mm.to_string(index=False))
    return "\n".join(lines)
