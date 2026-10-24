"""Flattening and PIR recomputation on a synthetic box score shaped like the v3 API."""
import json

import pandas as pd

from elfa.features import boxscores as bx


def _player(code, name, stats, start=True):
    return {
        "player": {"person": {"code": code, "name": name}, "positionName": "Guard", "dorsal": "1"},
        "stats": {**stats, "startFive": start},
    }


BASE = {
    "timePlayed": 1800, "valuation": 20, "points": 17, "fieldGoalsMade2": 4, "fieldGoalsAttempted2": 8,
    "fieldGoalsMade3": 2, "fieldGoalsAttempted3": 6, "freeThrowsMade": 3, "freeThrowsAttempted": 4,
    "totalRebounds": 10, "defensiveRebounds": 8, "offensiveRebounds": 2, "assistances": 2, "steals": 0,
    "turnovers": 1, "blocksFavour": 0, "blocksAgainst": 0, "foulsCommited": 3, "foulsReceived": 4,
    "plusMinus": 5,
}


def test_build_player_games(tmp_path, monkeypatch):
    raw = tmp_path / "raw"
    proc = tmp_path / "processed"
    proc.mkdir()
    monkeypatch.setattr(bx, "RAW", raw)
    monkeypatch.setattr(bx, "PROCESSED", proc)
    d = raw / "euroleague" / "E2026"
    (d / "boxscores").mkdir(parents=True)
    game = {
        "gameCode": 61, "round": 7, "phaseType": {"code": "RS"}, "utcDate": "2026-10-23T18:15:00Z",
        "played": True,
        "local": {"club": {"code": "OLY", "name": "Olympiacos Piraeus"}, "score": 61},
        "road": {"club": {"code": "ULK", "name": "Fenerbahce Beko Istanbul"}, "score": 64},
    }
    (d / "games.json").write_text(json.dumps([game]))
    bs = {
        "local": {"players": [_player("P1", "VEZENKOV, SASHA", BASE)], "team": {}},
        "road": {"players": [_player("P2", "BALDWIN, WADE", {**BASE, "timePlayed": "25:30", "valuation": 7,
                                                               "points": 5, "totalRebounds": 1,
                                                               "foulsReceived": 1}, start=False)], "team": {}},
    }
    (d / "boxscores" / "61.json").write_text(json.dumps(bs))

    df = bx.build_player_games(["E2026"])
    assert len(df) == 2
    v = df[df.player_code == "P1"].iloc[0]
    # 17+10+2+0+0+4 - (4+4+1+1+3+0) = 33 - 13 = 20  -> matches the platform's 20 for Vezenkov MD7
    assert v.pir == 20 and not v.pir_mismatch
    assert v.team == "OLY" and v.opponent == "ULK" and v.home and v.starter
    assert abs(v.minutes - 30.0) < 1e-9
    r = df[df.player_code == "P2"].iloc[0]
    assert abs(r.minutes - 25.5) < 1e-9 and not r.home and not r.starter
    assert (proc / "player_games.parquet").exists()
    assert pd.read_parquet(proc / "player_games.parquet").shape[0] == 2
