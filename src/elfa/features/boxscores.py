"""Flatten cached official box scores into one player-game table.

Output: data/processed/player_games.parquet with one row per player per game, both seasons.
PIR is recomputed from components and checked against the API's `valuation`.
"""
from __future__ import annotations

import json

import pandas as pd

from elfa.config import PROCESSED, RAW

STAT_MAP = {
    "timePlayed": "seconds",
    "valuation": "pir_api",
    "points": "pts",
    "fieldGoalsMade2": "fg2m", "fieldGoalsAttempted2": "fg2a",
    "fieldGoalsMade3": "fg3m", "fieldGoalsAttempted3": "fg3a",
    "freeThrowsMade": "ftm", "freeThrowsAttempted": "fta",
    "totalRebounds": "reb", "defensiveRebounds": "dreb", "offensiveRebounds": "oreb",
    "assistances": "ast", "steals": "stl", "turnovers": "tov",
    "blocksFavour": "blk", "blocksAgainst": "blk_against",
    "foulsCommited": "pf", "foulsReceived": "fd",
    "plusMinus": "plus_minus", "startFive": "starter",
}


def _parse_minutes(v) -> float:
    """timePlayed arrives as seconds (int) or 'MM:SS' depending on endpoint version."""
    if v is None:
        return 0.0
    if isinstance(v, (int, float)):
        return float(v) / 60.0
    if isinstance(v, str) and ":" in v:
        m, s = v.split(":")[:2]
        return int(m) + int(s) / 60.0
    try:
        return float(v) / 60.0
    except ValueError:
        return 0.0


def pir(row: pd.Series) -> float:
    pos = row.pts + row.reb + row.ast + row.stl + row.blk + row.fd
    neg = (
        (row.fg2a - row.fg2m) + (row.fg3a - row.fg3m) + (row.fta - row.ftm)
        + row.tov + row.pf + row.blk_against
    )
    return float(pos - neg)


def _side_rows(side: dict, game: dict, season: str, home: bool, opp_code: str) -> list[dict]:
    team_code = side["team"].get("code") if isinstance(side.get("team"), dict) else None
    rows = []
    for p in side.get("players", []):
        person = p["player"]["person"]
        st = p["stats"]
        row = {
            "season": season,
            "game_code": game["gameCode"],
            "round": game["round"],
            "phase": game["phaseType"]["code"],
            "date_utc": game["utcDate"],
            "team": team_code,
            "opponent": opp_code,
            "home": home,
            "player_code": person["code"],
            "player_name": person["name"],
            "position_api": p["player"].get("positionName"),
            "dorsal": p["player"].get("dorsal"),
        }
        for k, v in STAT_MAP.items():
            if v != "seconds":
                row[v] = st.get(k)
        row["minutes"] = _parse_minutes(st.get("timePlayed"))
        row["played"] = row["minutes"] > 0
        rows.append(row)
    return rows


def build_player_games(seasons: list[str]) -> pd.DataFrame:
    rows: list[dict] = []
    for season in seasons:
        d = RAW / "euroleague" / season
        games = {g["gameCode"]: g for g in json.loads((d / "games.json").read_text(encoding="utf-8"))}
        for fp in sorted((d / "boxscores").glob("*.json")):
            code = int(fp.stem)
            g = games.get(code)
            if g is None:
                continue
            bs = json.loads(fp.read_text(encoding="utf-8"))
            local_code = g["local"]["club"]["code"]
            road_code = g["road"]["club"]["code"]
            # the stats payload's team.code is unreliable on some seasons; trust the schedule
            for side_key, code_, opp, home in (
                ("local", local_code, road_code, True),
                ("road", road_code, local_code, False),
            ):
                side = bs.get(side_key) or {}
                side = {**side, "team": {**(side.get("team") or {}), "code": code_}}
                rows.extend(_side_rows(side, g, season, home, opp))
    df = pd.DataFrame(rows)
    num_cols = [c for c in STAT_MAP.values() if c not in ("seconds", "starter")]
    df[num_cols] = df[num_cols].apply(pd.to_numeric, errors="coerce").fillna(0)
    df["starter"] = df["starter"].fillna(False).astype(bool)
    df["pir"] = df.apply(pir, axis=1)
    df["pir_mismatch"] = (df["pir"] - df["pir_api"]).abs() > 0.5
    df["date_utc"] = pd.to_datetime(df["date_utc"], utc=True)
    df = df.sort_values(["season", "round", "game_code", "team", "minutes"], ascending=[True, True, True, True, False])
    out = PROCESSED / "player_games.parquet"
    df.to_parquet(out, index=False)
    return df


def summary(df: pd.DataFrame) -> str:
    by_season = df.groupby("season").agg(games=("game_code", "nunique"), rows=("player_code", "size"),
                                         mismatches=("pir_mismatch", "sum"))
    return by_season.to_string()
