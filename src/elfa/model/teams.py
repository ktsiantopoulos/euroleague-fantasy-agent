"""Team strength, game margin distribution, win probability and coach expected points.

Without odds: margin ~ Normal(mu, SIGMA) with mu from this season's net rating difference plus a
home edge. With odds (see ingest/odds.py): mu = -spread of the team, p_win from the moneyline.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass

import pandas as pd

from elfa.config import RAW

HOME_EDGE = 3.0      # points, EuroLeague home advantage
SIGMA = 12.0         # std dev of final margin
SHRINK_GAMES = 6     # net rating shrinkage toward 0

# coach scoring buckets (verified: win 1-10 +10, win 11-20 +20, loss 1-10 -5, loss 11-20 -10, loss 21+ -20)
COACH_BUCKETS = [(-999, -20.5, -20), (-20.5, -10.5, -10), (-10.5, 0, -5), (0, 10.5, 10), (10.5, 20.5, 20), (20.5, 999, 25)]
# NOTE: win by 21+ = +25 per the user (not yet observed in API data); the rest are verified from the API.


def _phi(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


@dataclass
class Game:
    game_code: int
    round: int
    date_utc: str
    home: str
    away: str


def load_schedule(season: str) -> list[dict]:
    return json.loads((RAW / "euroleague" / season / "games.json").read_text(encoding="utf-8"))


def team_ratings(pg: pd.DataFrame, schedule: list[dict]) -> pd.DataFrame:
    """Net rating per 100 possessions and pace, from played games of the season in `pg`."""
    score = {}
    for g in schedule:
        if g.get("played"):
            score[g["gameCode"]] = (g["local"]["club"]["code"], g["local"]["score"], g["road"]["club"]["code"], g["road"]["score"])
    team_games = pg.groupby(["game_code", "team"]).agg(
        fga=("fg2a", "sum"), fg3a=("fg3a", "sum"), fta=("fta", "sum"), tov=("tov", "sum"), oreb=("oreb", "sum")
    ).reset_index()
    team_games["poss"] = team_games.fga + team_games.fg3a + 0.44 * team_games.fta + team_games.tov - team_games.oreb
    rows = []
    for r in team_games.itertuples():
        s = score.get(r.game_code)
        if not s:
            continue
        pf, pa = (s[1], s[3]) if r.team == s[0] else (s[3], s[1])
        rows.append((r.team, r.game_code, pf, pa, r.poss))
    tg = pd.DataFrame(rows, columns=["team", "game_code", "pf", "pa", "poss"])
    t = tg.groupby("team").agg(games=("game_code", "nunique"), pf=("pf", "sum"), pa=("pa", "sum"), poss=("poss", "sum"))
    t["pace"] = t.poss / t.games
    t["ortg"] = 100 * t.pf / t.poss
    t["drtg"] = 100 * t.pa / t.poss
    t["net_raw"] = t.ortg - t.drtg
    w = t.games / (t.games + SHRINK_GAMES)
    t["net"] = w * t.net_raw
    t["league_pace"] = t.pace.mean()
    return t.reset_index()


def margin_mu(home: str, away: str, ratings: pd.DataFrame) -> float:
    r = ratings.set_index("team")
    nh = r.net.get(home, 0.0)
    na = r.net.get(away, 0.0)
    pace = (r.pace.get(home, r.pace.mean()) + r.pace.get(away, r.pace.mean())) / 2
    return (nh - na) * pace / 100 + HOME_EDGE


def win_prob(mu: float, sigma: float = SIGMA) -> float:
    return _phi(mu / sigma)


def coach_ev(mu: float, sigma: float = SIGMA) -> float:
    ev = 0.0
    for lo, hi, pts in COACH_BUCKETS:
        p = _phi((hi - mu) / sigma) - _phi((lo - mu) / sigma)
        ev += p * pts
    return ev


def matchday_games(schedule: list[dict], md_number: int) -> list[Game]:
    """Games of the fantasy matchday `md_number`.

    A platform matchday is exactly one EuroLeague regular-season round (38 matchdays = 38 rounds; the
    platform's `num_rounds` inside a matchday counts its game nights, not EuroLeague rounds). If that
    round is already fully played (stale market), fall back to the next unplayed round.
    """
    games = upcoming_rounds(schedule, 1, md_number)
    if games and any(not g_played(schedule, g.game_code) for g in games):
        return games
    return upcoming_rounds(schedule, 1)


def g_played(schedule: list[dict], game_code: int) -> bool:
    return any(g["gameCode"] == game_code and g.get("played") for g in schedule)


def turns_from_market(market: list[dict], team_map: pd.DataFrame) -> dict[str, int]:
    """Game night (turn) per official club code, from the platform's own sub-round number in the market
    (`round.number`: 1 = first night of the matchday). Empty when the market carries no round info."""
    t2o = dict(zip(team_map.platform_abbr, team_map.official_code))
    out: dict[str, int] = {}
    for m in market:
        abbr = (m.get("team") or {}).get("abbreviation")
        n = (m.get("round") or {}).get("number")
        if abbr in t2o and n:
            out[t2o[abbr]] = int(n)
    return out


def upcoming_rounds(schedule: list[dict], n_rounds: int, from_round: int | None = None) -> list[Game]:
    played_rounds = {g["round"] for g in schedule if g.get("played")}
    start = from_round or (max(played_rounds) + 1 if played_rounds else 1)
    out = []
    for g in schedule:
        if start <= g["round"] < start + n_rounds and g["phaseType"]["code"] == "RS":
            out.append(Game(g["gameCode"], g["round"], g["utcDate"], g["local"]["club"]["code"], g["road"]["club"]["code"]))
    return sorted(out, key=lambda x: (x.round, x.date_utc))
