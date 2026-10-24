"""Data access for the dashboard: everything comes from files the pipeline commits."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

DATA = ROOT / "data"
PROCESSED = DATA / "processed"
RAW = DATA / "raw"
PRICES = DATA / "prices"
REPORTS = ROOT / "reports"


def latest_matchday() -> int:
    dirs = sorted((RAW / "fantaking").glob("md_*"))
    return int(dirs[-1].name.split("_")[1]) if dirs else 0


def load_projection() -> tuple[int, pd.DataFrame]:
    md = latest_matchday()
    files = sorted(PROCESSED.glob("projection_md*.csv"))
    if not files:
        return md, pd.DataFrame()
    df = pd.read_csv(files[-1], dtype={"platform_id": str})
    df["games"] = df.games_json.map(lambda j: json.loads(j) if isinstance(j, str) else [])
    df["nights"] = df.games.map(lambda gs: "/".join(f"T{g['turn']}" for g in gs))
    md_file = int(files[-1].stem.split("md")[1])
    return md_file, df


def load_roster_state() -> tuple[dict, dict]:
    md = latest_matchday()
    d = RAW / "fantaking" / f"md_{md:02d}"
    tmd = json.loads((d / "team_matchday.json").read_text(encoding="utf-8")) if (d / "team_matchday.json").exists() else {}
    roster = json.loads((d / "roster.json").read_text(encoding="utf-8")) if (d / "roster.json").exists() else {"players": []}
    return tmd, roster


def load_report(name: str = "recommendation_latest.md") -> str:
    p = REPORTS / name
    return p.read_text(encoding="utf-8") if p.exists() else "_no report yet_"


def load_recommendation() -> dict:
    p = REPORTS / "recommendation_latest.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def load_csv(name: str, **kw) -> pd.DataFrame:
    p = PROCESSED / name
    return pd.read_csv(p, **kw) if p.exists() else pd.DataFrame()


def load_player_games() -> pd.DataFrame:
    """Current-season box scores only (rebuilt from the committed raw files; the parquet is not committed).

    Older seasons may exist under data/raw (kept solely so players without a game yet can be identity-mapped);
    they are never used for statistics — the model and every page filter to the latest season.
    """
    pq = PROCESSED / "player_games.parquet"
    seasons = sorted(p.name for p in (RAW / "euroleague").glob("E*") if (p / "games.json").exists())
    if not seasons:
        return pd.DataFrame()
    df = pd.DataFrame()
    if pq.exists():
        try:
            df = pd.read_parquet(pq)
        except Exception:  # noqa: BLE001, S110 - fall through to a rebuild from raw
            pass
    if df.empty:
        from elfa.features.boxscores import build_player_games

        df = build_player_games(seasons[-1:])
    return df[df.season == df.season.max()].reset_index(drop=True) if "season" in df else df


def load_schedule() -> list[dict]:
    seasons = sorted(p for p in (RAW / "euroleague").glob("E*") if (p / "games.json").exists())
    if not seasons:
        return []
    return json.loads((seasons[-1] / "games.json").read_text(encoding="utf-8"))


def load_prices() -> pd.DataFrame:
    files = sorted(PRICES.glob("md_*.csv"))
    if not files:
        return pd.DataFrame()
    return pd.concat([pd.read_csv(f, dtype={"player_id": str}) for f in files], ignore_index=True)


def load_schedule_df() -> pd.DataFrame:
    """One row per game of the current season: round, UTC date, official home/away codes, scores, played flag."""
    rows = []
    for g in load_schedule():
        rows.append({
            "game_code": g["gameCode"], "round": g["round"], "phase": g["phaseType"]["code"],
            "date_utc": pd.Timestamp(g["utcDate"]), "played": bool(g.get("played")),
            "home": g["local"]["club"]["code"], "away": g["road"]["club"]["code"],
            "home_name": g["local"]["club"]["name"], "away_name": g["road"]["club"]["name"],
            "home_score": g["local"].get("score"), "away_score": g["road"].get("score"),
            "venue": (g.get("venue") or {}).get("name"),
        })
    df = pd.DataFrame(rows)
    return df.sort_values(["round", "date_utc"]).reset_index(drop=True) if len(df) else df


def load_odds_snapshots() -> pd.DataFrame:
    """Every committed odds pull, parsed to one row per (snapshot, game) with the bookmaker consensus —
    the same numbers the projection used (elfa.ingest.odds.consensus)."""
    files = sorted((RAW / "odds").glob("odds_*.json"))
    if not files:
        return pd.DataFrame()
    from elfa.ingest.odds import consensus

    schedule = load_schedule()
    rows = []
    for fp in files:
        snap = pd.Timestamp(fp.stem.split("_")[1]).tz_localize("UTC")
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001, S112 - a half-written pull must not break the page
            continue
        for (home, away), rec in consensus(data if isinstance(data, list) else [], schedule).items():
            rows.append({"snapshot": snap, "home": home, "away": away, "commence": pd.Timestamp(rec.get("commence")),
                         "home_win_prob": rec["home_win_prob"], "home_spread": rec["home_spread"], "total": rec["total"], "books": rec["books"]})
    return pd.DataFrame(rows)


def pipeline_status() -> dict:
    txt = load_report("latest.md")
    first = txt.splitlines()[0] if txt else ""
    rec = load_report("recommendation_latest.md")
    gen = next((ln for ln in rec.splitlines() if ln.startswith("Generated")), "")
    dl = next((ln for ln in rec.splitlines() if ln.startswith("**Deadline")), "")
    return {"run_reason": first.replace("## ", ""), "generated": gen, "deadline": dl, "log": txt}
