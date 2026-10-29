"""Client for the fantasy platform backend (Dunkest "Fantaking" engine).

Read-only. Every call is a GET with the user's bearer token. Raw JSON is written to
data/raw/fantaking/md_<number>/ so a run is reproducible and a failed run leaves evidence.
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import os
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


def _load_schedule() -> list[dict]:
    """Official schedule pulled by `elfa pull-official` (runs before pull-platform); empty if absent."""
    fp = RAW / "euroleague" / os.getenv("SEASON_CODE", "E2026") / "games.json"
    try:
        return json.loads(fp.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []


def resolve_rollover(cfg: dict, schedule: list[dict], now: dt.datetime | None = None) -> tuple[dict, str | None]:
    """Detect a platform that has not yet rolled over to the next matchday.

    One fantasy matchday == one EuroLeague RS round. If every game of the platform's current matchday is
    already played and the next matchday exists, the platform is lagging: return a copy of the config pointed
    at the next matchday (previous_matchday = the finished one, deadline = first tip-off of the next round
    minus one minute, the platform's own convention) plus a note. Otherwise return (cfg, None) unchanged.
    """
    cur = cfg.get("current_matchday") or {}
    n = cur.get("number")
    if not n:
        return cfg, None
    rs = [g for g in schedule if (g.get("phaseType") or {}).get("code") == "RS"]
    this_round = [g for g in rs if g["round"] == n]
    if not this_round or not all(g.get("played") for g in this_round):
        return cfg, None
    nxt = next((m for m in cfg.get("matchdays", []) if m["number"] == n + 1), None)
    next_round = sorted((g for g in rs if g["round"] == n + 1), key=lambda g: g["utcDate"])
    if not nxt or not next_round:
        return cfg, None
    tip = dt.datetime.fromisoformat(next_round[0]["utcDate"].replace("Z", "+00:00"))
    if tip.tzinfo is None:
        tip = tip.replace(tzinfo=dt.UTC)
    now = now or dt.datetime.now(dt.UTC)
    if now >= tip:  # next round already under way - the platform should have rolled; don't guess
        return cfg, None
    deadline = (tip - dt.timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%S.000000Z")
    eff = dict(cfg)
    eff["current_matchday"] = {"id": nxt["id"], "number": nxt["number"],
                               "num_rounds": len({g["utcDate"][:10] for g in next_round})}
    eff["previous_matchday"] = {k: cur[k] for k in ("id", "number") if k in cur}
    eff["current_round"] = {"started_at": deadline, "derived_from": "schedule"}
    eff["rollover"] = {"platform_current": n, "used": n + 1, "deadline_utc": deadline}
    note = (f"platform still reports MD {n} (all games played) - rolled over to MD {n + 1}, "
            f"deadline {deadline[:16].replace('T', ' ')} UTC from the schedule")
    return eff, note


def pull_matchday(client: FantakingClient, md_id: int | None = None, with_history: bool = False) -> Path:
    """Pull league config, my team state, roster and the full market for one matchday.

    with_history=True also pulls each market player's fantasy-pts for every past matchday
    (358 players x N matchdays requests - run once, then incrementally).
    """
    raw_cfg = client.league_config()
    cfg = raw_cfg
    tmd = roster = market = None
    if md_id is None:
        eff, note = resolve_rollover(raw_cfg, _load_schedule())
        if note:
            new_id = eff["current_matchday"]["id"]
            try:  # fetch everything for the next matchday in memory first, so a failure leaves no half-written md_ dir
                tmd, roster, market = client.team_matchday(new_id), client.roster(new_id), client.market(new_id)
                if not market:
                    raise ValueError("empty market")
                cfg = eff
                print(f"  ! {note}")
            except (requests.HTTPError, ValueError, KeyError) as e:
                tmd = roster = market = None
                print(f"  ! platform lags (MD {raw_cfg['current_matchday']['number']} finished) but MD "
                      f"{eff['current_matchday']['number']} is not served yet ({type(e).__name__}) - pulling the stale matchday")
        md_id = cfg["current_matchday"]["id"]
    md_number = next((m["number"] for m in cfg["matchdays"] if m["id"] == md_id), md_id)
    out = RAW / "fantaking" / f"md_{md_number:02d}"
    pulled_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    _dump(out / "league_config.json", cfg)
    if cfg is not raw_cfg:
        _dump(out / "league_config_platform.json", raw_cfg)
    _dump(out / "team_matchday.json", tmd if tmd is not None else client.team_matchday(md_id))
    _dump(out / "roster.json", roster if roster is not None else client.roster(md_id))
    # The squad the platform last locked (previous matchday). Until this matchday's deadline every trade on
    # roster.json is reversible, so the optimiser's baseline is this squad with the full trade allowance.
    prev_md = cfg.get("previous_matchday") or {}
    if prev_md.get("id"):
        try:
            _dump(out / "roster_locked.json", client.roster(prev_md["id"]))
        except requests.HTTPError as e:  # first matchday of a phase etc. - the recommender falls back to roster.json
            _dump(out / "roster_locked.json", {"error": str(e), "players": []})
    if market is None:
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
