"""Client for the fantasy platform backend (Dunkest "Fantaking" engine).

Read-only. Every call is a GET with the user's bearer token. Raw JSON is written to
data/raw/fantaking/md_<number>/ so a run is reproducible and a failed run leaves evidence.
"""
from __future__ import annotations

import csv
import json
import time
from pathlib import Path
from typing import Any

import requests

from elfa.config import PRICES, RAW, Settings


class FantakingClient:
    def __init__(self, s: Settings, sleep: float = 0.4):
        self.s = s
        self.sleep = sleep
        self.sess = requests.Session()
        self.sess.headers.update(
            {"Authorization": f"Bearer {s.fantaking_token}", "Accept": "application/json"}
        )

    # ---- low level -------------------------------------------------------------------
    def get(self, path: str, **params: Any) -> dict:
        url = f"{self.s.fantaking_base}{path}"
        r = self.sess.get(url, params=params or None, timeout=30)
        if r.status_code == 401:
            raise RuntimeError("Fantaking token rejected (401) - refresh FANTAKING_TOKEN from the browser")
        r.raise_for_status()
        time.sleep(self.sleep)
        return r.json()

    # ---- endpoints -------------------------------------------------------------------
    def league_config(self) -> dict:
        return self.get(f"/api/v1/leagues/{self.s.league_id}/config")["data"]

    def game_config(self) -> dict:
        return self.get(f"/api/v1/games/{self.s.game_id}/config")["data"]

    def my_teams(self) -> list[dict]:
        return self.get("/api/v1/user/fantasy-teams", league=self.s.league_id, game_mode=1)["data"]

    def team_matchday(self, md_id: int) -> dict:
        return self.get(f"/api/v1/fantasy-teams/{self.s.fantasy_team_id}/matchdays/{md_id}")["data"]

    def roster(self, md_id: int) -> dict:
        return self.get(f"/api/v1/fantasy-teams/{self.s.fantasy_team_id}/matchdays/{md_id}/roster")["data"]

    def market(self, md_id: int, per_page: int = 100) -> list[dict]:
        out: list[dict] = []
        page = 1
        while True:
            j = self.get(
                f"/api/v1/players-lists/{self.s.players_list_id}/matchdays/{md_id}/players",
                per_page=per_page, page=page, sort_by="quotation", sort_order="desc",
            )
            out.extend(j["data"])
            meta = j.get("meta", {})
            if page >= int(meta.get("last_page", page)):
                break
            page += 1
        return out

    def player_fantasy_pts(self, player_id: int, md_id: int) -> dict:
        return self.get(
            f"/api/v1/players/{player_id}/fantasy-pts",
            league=self.s.league_id, matchday=md_id, lang="en",
        )["data"]

    def player_trend(self, player_id: int) -> Any:
        return self.get(f"/api/v1/players/{player_id}/trend", league=self.s.league_id)["data"]

    def player_upcoming(self, player_id: int) -> Any:
        return self.get(f"/api/v1/players/{player_id}/upcoming-matches", league=self.s.league_id)["data"]

    def player_profile(self, player_id: int) -> Any:
        return self.get(f"/api/v1/players/{player_id}/profile", league=self.s.league_id, lang="en")["data"]


# ---- pull orchestration ------------------------------------------------------------------

def _dump(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


def market_to_rows(market: list[dict], md_number: int, pulled_at: str) -> list[dict]:
    rows = []
    for p in market:
        rows.append(
            {
                "matchday": md_number,
                "pulled_at": pulled_at,
                "player_id": p["id"],
                "first_name": p.get("first_name"),
                "last_name": p.get("last_name"),
                "position": (p.get("position") or {}).get("name"),
                "team": (p.get("team") or {}).get("abbreviation"),
                "home_away": (p.get("team") or {}).get("position"),
                "opponent": (p.get("opponent") or {}).get("abbreviation"),
                "quotation": p.get("quotation"),
                "avg_pts": p.get("avg_pts"),
                "popularity": p.get("popularity"),
                "is_injured": p.get("is_injured"),
                "probability_of_playing": p.get("probability_of_playing"),
                "is_on_fire": p.get("is_on_fire"),
            }
        )
    return rows


def pull_matchday(client: FantakingClient, md_id: int | None = None, with_history: bool = False) -> Path:
    """Pull league config, my team state, roster and the full market for one matchday.

    with_history=True also pulls each market player's fantasy-pts for every past matchday
    (358 players x N matchdays requests - run once, then incrementally).
    """
    cfg = client.league_config()
    if md_id is None:
        md_id = cfg["current_matchday"]["id"]
    md_number = next((m["number"] for m in cfg["matchdays"] if m["id"] == md_id), md_id)
    out = RAW / "fantaking" / f"md_{md_number:02d}"
    pulled_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    _dump(out / "league_config.json", cfg)
    _dump(out / "team_matchday.json", client.team_matchday(md_id))
    _dump(out / "roster.json", client.roster(md_id))
    market = client.market(md_id)
    _dump(out / "market.json", market)

    # price log: committed to git, one file per matchday pull
    rows = market_to_rows(market, md_number, pulled_at)
    price_file = PRICES / f"md_{md_number:02d}.csv"
    with price_file.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    # per-player fantasy points: always keep the previous matchday current (needed by `elfa evaluate`);
    # --history backfills every past matchday
    hist_dir = RAW / "fantaking" / "fantasy_pts"
    prev = cfg.get("previous_matchday") or {}
    targets = [m for m in cfg["matchdays"] if m["number"] < md_number] if with_history else (
        [m for m in cfg["matchdays"] if m["id"] == prev.get("id")] if prev else [])
    if targets:
        for p in market:
            for m in targets:
                fp = hist_dir / f"{p['id']}_md{m['number']:02d}.json"
                if fp.exists():
                    continue
                try:
                    _dump(fp, client.player_fantasy_pts(p["id"], m["id"]))
                except requests.HTTPError as e:  # DNP / no match -> keep going
                    _dump(fp, {"error": str(e)})
    return out
