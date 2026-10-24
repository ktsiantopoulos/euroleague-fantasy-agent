"""Bookmaker odds via the-odds-api.com (sport key `basketball_euroleague`).

Optional: skipped when ODDS_API_KEY is absent. Returns per game: consensus spread (home team
perspective, negative = home favourite), total, and implied home win probability (vig removed).
Team names are matched to official club codes by token overlap with the schedule's club names.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import requests

from elfa.config import RAW
from elfa.features.mapping import norm

API = "https://api.the-odds-api.com/v4/sports/basketball_euroleague/odds"


def _club_index(schedule: list[dict]) -> dict[str, set[str]]:
    idx = {}
    for g in schedule:
        for side in ("local", "road"):
            c = g[side]["club"]
            idx[c["code"]] = {t for t in norm(c["name"]).split() if len(t) > 2} | {norm(c["code"])}
    return idx


def _match(name: str, idx: dict[str, set[str]]) -> str | None:
    toks = {t for t in norm(name).split() if len(t) > 2}
    best, n = None, 0
    for code, ctoks in idx.items():
        k = len(toks & ctoks)
        if k > n:
            best, n = code, k
    return best


def fetch_odds(schedule: list[dict], out_dir: Path) -> dict[tuple[str, str], dict]:
    key = os.getenv("ODDS_API_KEY", "").strip()
    if not key:
        return {}
    r = requests.get(API, params={"apiKey": key, "regions": "eu", "markets": "h2h,spreads,totals", "oddsFormat": "decimal"}, timeout=30)
    if r.status_code != 200:
        print(f"  ! odds API {r.status_code}: {r.text[:120]}")
        return {}
    data = r.json()
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"odds_{time.strftime('%Y%m%dT%H%M', time.gmtime())}.json").write_text(json.dumps(data), encoding="utf-8")
    idx = _club_index(schedule)
    out: dict[tuple[str, str], dict] = {}
    for ev in data:
        home = _match(ev["home_team"], idx)
        away = _match(ev["away_team"], idx)
        if not home or not away:
            continue
        ph, spreads, totals = [], [], []
        for bk in ev.get("bookmakers", []):
            for m in bk.get("markets", []):
                oc = {o["name"]: o for o in m.get("outcomes", [])}
                if m["key"] == "h2h" and ev["home_team"] in oc and ev["away_team"] in oc:
                    a, b = 1 / oc[ev["home_team"]]["price"], 1 / oc[ev["away_team"]]["price"]
                    ph.append(a / (a + b))
                elif m["key"] == "spreads" and ev["home_team"] in oc:
                    spreads.append(float(oc[ev["home_team"]]["point"]))
                elif m["key"] == "totals":
                    pts = [float(o["point"]) for o in m.get("outcomes", []) if "point" in o]
                    if pts:
                        totals.append(sum(pts) / len(pts))
        rec = {
            "home_win_prob": sum(ph) / len(ph) if ph else None,
            "home_spread": sum(spreads) / len(spreads) if spreads else None,
            "total": sum(totals) / len(totals) if totals else None,
            "books": len(ev.get("bookmakers", [])),
            "commence": ev.get("commence_time"),
        }
        out[(home, away)] = rec
    return out


def odds_dir() -> Path:
    return RAW / "odds"
