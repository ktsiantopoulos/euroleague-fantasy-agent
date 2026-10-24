"""Committed matchday calendar: fantasy matchday -> EuroLeague round -> game nights (turns).

One fantasy matchday is one EuroLeague regular-season round. Turns are the distinct game dates of
that round in order; for the matchday the market was pulled for, the platform's own sub-round number
per club overrides the date order (they have agreed so far, but the platform is authoritative).

The table is rebuilt by `elfa build` and written to data/processed/matchdays.csv (committed), merging
with the previous version so platform-only facts (matchday id, deadline) survive once seen.
"""
from __future__ import annotations

import pandas as pd

from elfa.config import PROCESSED
from elfa.model.teams import turns_from_market

COLUMNS = ["matchday", "matchday_id", "round", "turn", "date_utc", "games", "first_tipoff_utc", "deadline_utc", "turn_source"]


def build_matchdays(schedule: list[dict], cfg: dict | None = None, market: list[dict] | None = None,
                    team_map: pd.DataFrame | None = None, previous: pd.DataFrame | None = None) -> pd.DataFrame:
    rs = [g for g in schedule if g["phaseType"]["code"] == "RS"]
    rows = []
    md_ids = {int(m["number"]): int(m["id"]) for m in (cfg or {}).get("matchdays", [])}
    cur = (cfg or {}).get("current_matchday") or {}
    cur_md = int(cur["number"]) if cur.get("number") else None
    deadline = ((cfg or {}).get("current_round") or {}).get("started_at")
    turns = turns_from_market(market or [], team_map) if market and team_map is not None else {}

    for rnd in sorted({g["round"] for g in rs}):
        games = sorted((g for g in rs if g["round"] == rnd), key=lambda g: g["utcDate"])
        dates = sorted({g["utcDate"][:10] for g in games})
        date_turn = {d: i + 1 for i, d in enumerate(dates)}
        per_turn: dict[int, list[dict]] = {}
        source = "schedule"
        for g in games:
            t = None
            if rnd == cur_md and turns:
                t = turns.get(g["local"]["club"]["code"]) or turns.get(g["road"]["club"]["code"])
                source = "platform" if t else source
            per_turn.setdefault(t or date_turn[g["utcDate"][:10]], []).append(g)
        for t in sorted(per_turn):
            gs = per_turn[t]
            rows.append({
                "matchday": rnd, "matchday_id": md_ids.get(rnd), "round": rnd, "turn": t,
                "date_utc": min(g["utcDate"][:10] for g in gs), "games": len(gs),
                "first_tipoff_utc": min(g["utcDate"] for g in gs),
                "deadline_utc": deadline if rnd == cur_md else None, "turn_source": source,
            })
    df = pd.DataFrame(rows, columns=COLUMNS)
    if previous is not None and len(previous):
        prev = previous.drop_duplicates(["matchday", "turn"]).set_index(["matchday", "turn"])
        keys = list(zip(df.matchday, df.turn))
        for col in ("matchday_id", "deadline_utc"):
            if col in prev:
                old = prev[col].to_dict()
                filled = pd.Series([old.get(k) for k in keys], index=df.index)
                df[col] = df[col].where(df[col].notna(), filled)
        if "turn_source" in prev:  # a turn split the platform confirmed once stays confirmed
            old = prev["turn_source"].to_dict()
            df["turn_source"] = ["platform" if old.get(k) == "platform" else s for k, s in zip(keys, df.turn_source)]
    df["matchday_id"] = df.matchday_id.astype("Int64")
    return df


def write_matchdays(schedule: list[dict], cfg: dict | None, market: list[dict] | None, team_map: pd.DataFrame | None) -> pd.DataFrame:
    fp = PROCESSED / "matchdays.csv"
    previous = pd.read_csv(fp) if fp.exists() else None
    df = build_matchdays(schedule, cfg, market, team_map, previous)
    df.to_csv(fp, index=False)
    return df


def load_matchdays() -> pd.DataFrame:
    fp = PROCESSED / "matchdays.csv"
    return pd.read_csv(fp, dtype={"date_utc": str}) if fp.exists() else pd.DataFrame(columns=COLUMNS)


def matchday_turns(md: int, table: pd.DataFrame | None = None) -> tuple[list[int], list[str]]:
    """(rounds, night dates in turn order) for a matchday from the committed table; empty if unknown."""
    t = load_matchdays() if table is None else table
    t = t[t.matchday == md].sort_values("turn")
    return (sorted(t["round"].unique().astype(int).tolist()), t.date_utc.tolist()) if len(t) else ([], [])
