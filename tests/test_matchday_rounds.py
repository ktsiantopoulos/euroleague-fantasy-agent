"""One fantasy matchday == one EuroLeague round; the platform's sub-rounds are game nights (turns)."""
import json

import pandas as pd

from elfa.config import RAW
from elfa.model.teams import matchday_games, turns_from_market


def _schedule(as_of_round: int | None = None):
    """Committed schedule; `as_of_round` replays it as it stood before that round tipped off (rounds >= it unplayed),
    so the tests don't break as the season advances."""
    sched = json.loads((RAW / "euroleague" / "E2026" / "games.json").read_text(encoding="utf-8"))
    if as_of_round:
        sched = [dict(g, played=g.get("played") and g["round"] < as_of_round) for g in sched]
    return sched


def test_matchday_is_exactly_one_round():
    sched = _schedule(as_of_round=8)
    games = matchday_games(sched, 8)
    assert {g.round for g in games} == {8}
    assert len(games) == 10
    # a double EuroLeague round must never be glued into one matchday
    assert len({g.date_utc[:10] for g in games}) == 2


def test_matchday_falls_back_to_next_unplayed_round_when_stale():
    sched = _schedule()
    games = matchday_games(sched, 3)  # already played
    assert games and all(g.round == min(x["round"] for x in sched if not x["played"]) for g in games)


def test_platform_turns_match_game_nights():
    market = json.loads((RAW / "fantaking" / "md_08" / "market.json").read_text(encoding="utf-8"))
    team_map = pd.read_csv(RAW.parent / "processed" / "team_map.csv")
    turns = turns_from_market(market, team_map)
    assert set(turns.values()) == {1, 2}
    night = {"2026-10-27": 1, "2026-10-28": 2}
    for g in matchday_games(_schedule(as_of_round=8), 8):
        assert turns[g.home] == turns[g.away] == night[g.date_utc[:10]]


def test_turns_empty_without_round_info():
    assert turns_from_market([{"team": {"abbreviation": "OLY"}}], pd.DataFrame({"platform_abbr": ["OLY"], "official_code": ["OLY"]})) == {}


def test_matchday_table_one_round_per_matchday_and_platform_turns():
    from elfa.features.matchdays import build_matchdays

    market = json.loads((RAW / "fantaking" / "md_08" / "market.json").read_text(encoding="utf-8"))
    cfg = json.loads((RAW / "fantaking" / "md_08" / "league_config.json").read_text(encoding="utf-8"))
    team_map = pd.read_csv(RAW.parent / "processed" / "team_map.csv")
    t = build_matchdays(_schedule(), cfg, market, team_map)
    assert t.matchday.nunique() == 38 and (t.matchday == t["round"]).all()
    md8 = t[t.matchday == 8]
    assert md8.turn.tolist() == [1, 2] and md8.date_utc.tolist() == ["2026-10-27", "2026-10-28"]
    assert (md8.turn_source == "platform").all() and md8.deadline_utc.notna().all()
    # rebuilding without platform data keeps what the platform once confirmed
    again = build_matchdays(_schedule(), None, None, None, previous=t)
    assert again[again.matchday == 8].turn_source.eq("platform").all()
    assert again[again.matchday == 8].deadline_utc.notna().all()
    assert int(again[again.matchday == 8].matchday_id.iloc[0]) == 1535
