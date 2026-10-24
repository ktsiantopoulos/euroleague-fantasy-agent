"""Client for the official EuroLeague API (public, no auth).

Schedule comes from v2 (`/v2/competitions/E/seasons/{season}/games`), box scores from v3
(`/v3/competitions/E/seasons/{season}/games/{gameCode}/stats`). Raw JSON is cached under
data/raw/euroleague/<season>/ and only missing played games are fetched on re-runs.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import requests

from elfa.config import RAW, Settings


class EuroleagueClient:
    def __init__(self, s: Settings, sleep: float = 0.3):
        self.base = s.el_base.rstrip("/")
        self.sleep = sleep
        self.sess = requests.Session()
        self.sess.headers.update({"Accept": "application/json"})

    def _get(self, path: str, **params) -> dict:
        r = self.sess.get(f"{self.base}{path}", params=params or None, timeout=60)
        r.raise_for_status()
        time.sleep(self.sleep)
        return r.json()

    def games(self, season: str) -> list[dict]:
        return self._get(f"/v2/competitions/E/seasons/{season}/games")["data"]

    def boxscore(self, season: str, game_code: int) -> dict:
        return self._get(f"/v3/competitions/E/seasons/{season}/games/{game_code}/stats")

    def team_advanced(self, season: str) -> dict:
        return self._get(
            "/v3/competitions/E/statistics/teams/advanced",
            seasonMode="Range", fromSeasonCode=season, toSeasonCode=season,
        )


def season_dir(season: str) -> Path:
    d = RAW / "euroleague" / season
    (d / "boxscores").mkdir(parents=True, exist_ok=True)
    return d


def pull_season(client: EuroleagueClient, season: str, force_schedule: bool = True) -> tuple[int, int]:
    """Refresh the schedule and fetch box scores for played games not yet cached.

    Returns (games_played, boxscores_fetched_now).
    """
    d = season_dir(season)
    sched = d / "games.json"
    if force_schedule or not sched.exists():
        games = client.games(season)
        sched.write_text(json.dumps(games, ensure_ascii=False), encoding="utf-8")
    else:
        games = json.loads(sched.read_text(encoding="utf-8"))

    played = [g for g in games if g.get("played")]
    fetched = 0
    for g in played:
        fp = d / "boxscores" / f"{g['gameCode']}.json"
        if fp.exists():
            continue
        try:
            bs = client.boxscore(season, g["gameCode"])
        except requests.HTTPError as e:
            print(f"  ! {season} game {g['gameCode']}: {e}")
            continue
        fp.write_text(json.dumps(bs, ensure_ascii=False), encoding="utf-8")
        fetched += 1
    return len(played), fetched
