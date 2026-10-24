"""Configuration: paths and environment."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

DATA = ROOT / "data"
RAW = DATA / "raw"
PROCESSED = DATA / "processed"
PRICES = DATA / "prices"
for _p in (RAW, PROCESSED, PRICES):
    _p.mkdir(parents=True, exist_ok=True)


def _env(name: str, default: str | None = None) -> str:
    v = os.getenv(name, default)
    if v is not None:
        v = v.strip()
    if v is None or v == "":
        raise RuntimeError(f"Missing env var {name} (see .env.example)")
    return v


@dataclass(frozen=True)
class Settings:
    fantaking_token: str
    fantaking_base: str
    game_id: int
    league_id: int
    players_list_id: int
    fantasy_team_id: int
    el_base: str
    season: str
    prior_season: str

    @classmethod
    def load(cls) -> Settings:
        return cls(
            fantaking_token=_env("FANTAKING_TOKEN"),
            fantaking_base=_env("FANTAKING_BASE", "https://fantaking-api.dunkest.com"),
            game_id=int(_env("FANTAKING_GAME_ID", "7")),
            league_id=int(_env("FANTAKING_LEAGUE_ID", "10")),
            players_list_id=int(_env("FANTAKING_PLAYERS_LIST_ID", "49")),
            fantasy_team_id=int(_env("FANTASY_TEAM_ID")),
            el_base=_env("EUROLEAGUE_API_BASE", "https://api-live.euroleague.net"),
            season=_env("SEASON_CODE", "E2026"),
            prior_season=_env("PRIOR_SEASON_CODE", "E2025"),
        )

    @classmethod
    def public_only(cls) -> Settings:
        """Settings for commands that only touch the public EuroLeague API."""
        return cls(
            fantaking_token="",
            fantaking_base="",
            game_id=7,
            league_id=10,
            players_list_id=49,
            fantasy_team_id=0,
            el_base=os.getenv("EUROLEAGUE_API_BASE", "https://api-live.euroleague.net"),
            season=os.getenv("SEASON_CODE", "E2026"),
            prior_season=os.getenv("PRIOR_SEASON_CODE", "E2025"),
        )
