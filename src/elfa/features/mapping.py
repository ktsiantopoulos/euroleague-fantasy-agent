"""Identity mapping between the fantasy platform and the official API.

Teams: platform abbreviation (e.g. FBT) -> official club code (e.g. ULK).
Players: platform player_id -> official person code, matched by normalised surname + team,
with a manual override file at data/processed/player_overrides.csv (platform_id,person_code).
"""
from __future__ import annotations

import json
import re
import unicodedata

import pandas as pd

from elfa.config import PROCESSED, RAW

# Seed: platform abbreviation -> official code. Verified by name matching at build time;
# anything that disagrees is reported, not silently trusted.
TEAM_SEED = {
    "EFS": "IST", "MIL": "MIL", "BJK": "BES", "CZV": "RED", "DUB": "DUB", "BAR": "BAR",
    "BAY": "MUN", "FBT": "ULK", "HTA": "HTA", "KBA": "BAS", "ASV": "ASV", "MTA": "TEL",
    "OLY": "OLY", "PAO": "PAN", "PBB": "PRS", "PAR": "PAR", "RMB": "MAD", "VBC": "PAM",
    "VIR": "VIR", "ZAL": "ZAL",
}

_STOP = {"basketball", "bc", "fc", "club", "istanbul", "belgrade", "tel", "aviv", "munich", "madrid",
         "berlin", "milan", "milano", "bologna", "kaunas", "piraeus", "athens", "vitoria", "gasteiz",
         "villeurbanne", "paris", "dubai", "valencia", "barcelona"}


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9 ]", " ", s.lower()).strip()


def _tokens(name: str) -> set[str]:
    return {t for t in norm(name).split() if len(t) > 2}


def map_teams(platform_teams: list[dict], official_games: list[dict]) -> pd.DataFrame:
    """Return a table platform_abbr, platform_name, official_code, official_name, method."""
    official: dict[str, str] = {}
    for g in official_games:
        for side in ("local", "road"):
            c = g[side]["club"]
            official[c["code"]] = c["name"]
    rows = []
    for t in platform_teams:
        abbr, pname = t["abbreviation"], t["name"]
        seed = TEAM_SEED.get(abbr)
        # name-based candidate: most shared tokens
        best, best_n = None, 0
        pt = _tokens(pname)
        for code, oname in official.items():
            n = len(pt & _tokens(oname))
            if n > best_n:
                best, best_n = code, n
        if seed and seed in official and (best == seed or best_n == 0):
            rows.append((abbr, pname, seed, official[seed], "seed"))
        elif best and best_n > 0:
            rows.append((abbr, pname, best, official[best], "name" if not seed else f"name (seed {seed} disagreed)"))
        else:
            rows.append((abbr, pname, seed, official.get(seed, "?"), "UNRESOLVED"))
    df = pd.DataFrame(rows, columns=["platform_abbr", "platform_name", "official_code", "official_name", "method"])
    df.to_csv(PROCESSED / "team_map.csv", index=False)
    return df


_SUFFIX = {"jr", "sr", "ii", "iii", "iv", "v"}


def _surname_key(last_name: str) -> str:
    toks = [t for t in norm(last_name).split() if t not in _SUFFIX]
    return "".join(toks)


def map_players(market: list[dict], player_games: pd.DataFrame, team_map: pd.DataFrame) -> pd.DataFrame:
    """Match platform players to official person codes by surname + team (current season only)."""
    t2o = dict(zip(team_map.platform_abbr, team_map.official_code))
    cur_season = player_games.season.max()

    def _index(df):
        # official surname = part before the comma in "SURNAME, NAME"
        return (
            df.assign(surname=df.player_name.str.split(",").str[0].map(_surname_key))
            .groupby(["team", "surname", "player_code", "player_name"], as_index=False)
            .agg(games=("game_code", "nunique"), minutes=("minutes", "sum"))
        )

    off = _index(player_games[player_games.season == cur_season])
    off_any = _index(player_games)  # any team this season, for transferred players with 0 games at the new club
    overrides_fp = PROCESSED / "player_overrides.csv"
    overrides = {}
    if overrides_fp.exists():
        o = pd.read_csv(overrides_fp, dtype=str)
        overrides = dict(zip(o.platform_id, o.person_code))

    rows = []
    for p in market:
        pid = str(p["id"])
        team_off = t2o.get((p.get("team") or {}).get("abbreviation"))
        key = _surname_key(p.get("last_name", ""))
        if pid in overrides:
            rows.append((pid, p.get("first_name"), p.get("last_name"), team_off, overrides[pid], "override"))
            continue
        if (p.get("position") or {}).get("name") == "Head Coach":
            rows.append((pid, p.get("first_name"), p.get("last_name"), team_off, None, "coach"))
            continue
        cand = off[(off.team == team_off) & (off.surname == key)]
        if len(cand) == 1:
            rows.append((pid, p.get("first_name"), p.get("last_name"), team_off, cand.player_code.iloc[0], "surname+team"))
        elif len(cand) > 1:
            # disambiguate by first-name token
            fn = norm(p.get("first_name", "")).split()[:1]
            c2 = cand[cand.player_name.map(norm).str.contains(fn[0])] if fn else cand
            if len(c2) == 1:
                rows.append((pid, p.get("first_name"), p.get("last_name"), team_off, c2.player_code.iloc[0], "surname+team+first"))
            else:
                rows.append((pid, p.get("first_name"), p.get("last_name"), team_off, None, "AMBIGUOUS"))
        else:
            # no games yet this season: look across all teams this season, disambiguate by first name
            fn = norm(p.get("first_name", "")).split()[:1]
            c3 = off_any[off_any.surname == key]
            if fn and len(c3) > 1:
                c3 = c3[c3.player_name.map(norm).str.contains(fn[0])]
            codes = c3.player_code.unique()
            if len(codes) == 1:
                rows.append((pid, p.get("first_name"), p.get("last_name"), team_off, codes[0], "surname+any-team"))
            else:
                rows.append((pid, p.get("first_name"), p.get("last_name"), team_off, None, "UNMATCHED"))
    df = pd.DataFrame(rows, columns=["platform_id", "first_name", "last_name", "official_team", "person_code", "method"])
    df.to_csv(PROCESSED / "player_map.csv", index=False)
    return df


def load_latest_market() -> tuple[int, list[dict], dict]:
    dirs = sorted((RAW / "fantaking").glob("md_*"))
    if not dirs:
        raise FileNotFoundError("No platform pull found - run `elfa pull-platform` first")
    d = dirs[-1]
    md = int(d.name.split("_")[1])
    market = json.loads((d / "market.json").read_text(encoding="utf-8"))
    cfg = json.loads((d / "league_config.json").read_text(encoding="utf-8"))
    return md, market, cfg
