"""Data access for the dashboard: everything comes from files the pipeline commits."""
from __future__ import annotations

import importlib
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


_ELFA_MTIME: dict[str, float] = {}


def elfa_attr(module: str, name: str):
    """Import `name` from an elfa module, reloading the module when its source changed on disk.

    Streamlit Cloud re-imports app/*.py on every push but keeps the src/elfa modules already in
    sys.modules, so a new function or a changed signature in elfa breaks until the app is rebooted.
    The module is reloaded on first use after each import of this file and whenever its source mtime changes.
    """
    mod = importlib.import_module(module)
    try:
        mtime = Path(mod.__file__).stat().st_mtime
    except (AttributeError, OSError):
        mtime = None
    # first sighting after a (re)deploy counts as stale too: data.py was re-imported but the elfa module was not
    if _ELFA_MTIME.get(module) != mtime or not hasattr(mod, name):
        mod = importlib.reload(mod)
    if mtime is not None:
        _ELFA_MTIME[module] = mtime
    return getattr(mod, name)


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
    return md_file, enrich_projection(df)


def load_market() -> list[dict]:
    md = latest_matchday()
    fp = RAW / "fantaking" / f"md_{md:02d}" / "market.json"
    return json.loads(fp.read_text(encoding="utf-8")) if fp.exists() else []


def enrich_projection(df: pd.DataFrame) -> pd.DataFrame:
    """Add the decision columns the pages show on top of the model output: floor, usage / role signal,
    fouls drawn and blocks against, season-start price and change, platform bench flag, risk badges."""
    df = df.copy()
    df["floor"] = (df.md_pts - 1.2816 * df.md_sd).round(1)
    pm = load_csv("player_map.csv", dtype={"platform_id": str, "person_code": str})
    u = load_csv("usage.csv", dtype={"player_code": str})
    if len(pm) and len(u):
        code = dict(zip(pm.platform_id.astype(str), pm.person_code))
        u = u.set_index("player_code")
        for col, name in (("shot_share", "shot_share"), ("fga_per_min", "fga_per_min"), ("usage_delta_last3", "usage_delta"),
                          ("min_delta_last3", "min_delta"), ("role_signal", "role_signal"), ("fd_pg", "fd_pg"), ("blka_pg", "blka_pg"),
                          ("starter_last", "starter_last")):
            df[name] = df.platform_id.astype(str).map(code).map(u[col])
    pb = load_csv("../prices/price_base.csv", dtype={"player_id": str}) if (PRICES / "price_base.csv").exists() else pd.DataFrame()
    if len(pb):
        df["price_base"] = df.platform_id.astype(str).map(dict(zip(pb.player_id, pb.price_base)))
        df["price_delta"] = (df.quotation - df.price_base).round(1)
    bench = {str(m["id"]): bool(m.get("started_from_bench")) for m in load_market()}
    if bench:
        df["bench_platform"] = df.platform_id.astype(str).map(bench)

    def _risk(r) -> str:
        tags = []
        if r.get("prob_play", 1) < 1:
            tags.append("doubtful")
        fl = str(r.get("flags") or "")
        if "DNP" in fl:
            tags.append("DNP last")
        if "only" in fl:
            tags.append("few games")
        if r.get("role_signal") == "falling":
            tags.append("usage falling")
        if r.get("role_signal") == "rising":
            tags.append("usage rising")
        return " · ".join(tags)

    df["risk"] = df.apply(_risk, axis=1)
    return df


def load_roster_state() -> tuple[dict, dict]:
    md = latest_matchday()
    d = RAW / "fantaking" / f"md_{md:02d}"
    tmd = json.loads((d / "team_matchday.json").read_text(encoding="utf-8")) if (d / "team_matchday.json").exists() else {}
    roster = json.loads((d / "roster.json").read_text(encoding="utf-8")) if (d / "roster.json").exists() else {"players": []}
    return tmd, roster


def load_locked_roster() -> dict:
    """The squad the platform last locked (previous matchday); {"players": []} if the pull predates this feature."""
    d = RAW / "fantaking" / f"md_{latest_matchday():02d}"
    f = d / "roster_locked.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {"players": []}


def trade_baseline():
    """Baseline squad + trade allowance for the what-if page (same rule as the recommender)."""
    md = latest_matchday()
    d = RAW / "fantaking" / f"md_{md:02d}"
    tmd, _ = load_roster_state()
    cfg = json.loads((d / "league_config.json").read_text(encoding="utf-8")) if (d / "league_config.json").exists() else {}
    market = json.loads((d / "market.json").read_text(encoding="utf-8")) if (d / "market.json").exists() else []
    fn = elfa_attr("elfa.model.baseline", "trade_baseline")
    return fn(d, tmd, cfg, {str(p["id"]) for p in market})


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
        build_player_games = elfa_attr("elfa.features.boxscores", "build_player_games")
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
    consensus = elfa_attr("elfa.ingest.odds", "consensus")
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


def platform_token() -> str:
    """FANTAKING_TOKEN from Streamlit secrets (Cloud) or the environment (.env locally); empty if absent."""
    import os

    tok = ""
    try:
        import streamlit as st

        tok = str(st.secrets.get("FANTAKING_TOKEN", "")) if hasattr(st, "secrets") else ""
    except Exception:  # noqa: BLE001 - no secrets file locally
        tok = ""
    return (tok or os.getenv("FANTAKING_TOKEN", "")).strip()


def refresh_team() -> dict:
    """Pull my team, roster and the market from the platform now and re-run the recommendation in-process.

    Writes into this container's data/ and reports/ (not committed): the dashboard shows the fresh state until
    the next pipeline run or redeploy replaces it. Returns a short status dict.
    """
    import os
    import time

    tok = platform_token()
    if not tok:
        return {"ok": False, "msg": "No FANTAKING_TOKEN in the app secrets (Streamlit Cloud → Manage app → Settings → Secrets)."}
    os.environ["FANTAKING_TOKEN"] = tok
    try:
        import streamlit as st

        for k in ("ODDS_API_KEY", "FANTASY_TEAM_ID"):
            if k in st.secrets:
                os.environ[k] = str(st.secrets[k])
    except Exception:  # noqa: BLE001, S110 - optional secrets
        pass
    os.environ.setdefault("FANTASY_TEAM_ID", "2787922")
    t0 = time.time()
    Settings = elfa_attr("elfa.config", "Settings")
    FantakingClient = elfa_attr("elfa.ingest.fantaking", "FantakingClient")
    pull_matchday = elfa_attr("elfa.ingest.fantaking", "pull_matchday")
    try:
        pull_matchday(FantakingClient(Settings.load()))
    except Exception as e:  # noqa: BLE001 - surface the reason in the page
        return {"ok": False, "msg": f"Platform pull failed: {type(e).__name__}: {str(e)[:160]}"}
    # the optimiser reads the parquet; rebuild it from the committed box scores if this container has none
    pq = PROCESSED / "player_games.parquet"
    if not pq.exists():
        build_player_games = elfa_attr("elfa.features.boxscores", "build_player_games")
        seasons = sorted(p.name for p in (RAW / "euroleague").glob("E*") if (p / "games.json").exists())
        build_player_games(seasons[-1:]).to_parquet(pq, index=False)
    try:
        recommend = elfa_attr("elfa.report.recommend", "recommend")
        recommend()
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "msg": f"Roster refreshed but the recommendation failed: {type(e).__name__}: {str(e)[:160]}"}
    tmd, roster = load_roster_state()
    coach = next((f"{p['first_name']} {p['last_name']}" for p in roster.get("players", []) if (p.get("position") or {}).get("name") == "Head Coach"), "—")
    return {"ok": True, "msg": f"Refreshed in {time.time() - t0:.0f}s · credits {tmd.get('credits')} · {tmd.get('trades')}/{tmd.get('max_num_trades_per_matchday')} trades pending (reversible until the deadline) · coach {coach}",
            "pulled_at": time.strftime("%H:%M:%S UTC", time.gmtime())}


def team_names() -> dict[str, str]:
    """Club name for every code in use — platform abbreviations (BJK, PAO) and official codes (BES, PAN).

    Uses the official API's short form ("Baskonia", "Crvena Zvezda") rather than the full sponsored name,
    so grid cells and cards stay readable on a phone.
    """
    short: dict[str, str] = {}
    full: dict[str, str] = {}
    for g in load_schedule():
        for side in ("local", "road"):
            c = g[side]["club"]
            short.setdefault(c["code"], c.get("abbreviatedName") or c["name"])
            full.setdefault(c["code"], c["name"])
    names: dict[str, str] = dict(short)
    tm = load_csv("team_map.csv")
    for r in tm.itertuples():
        code = str(r.official_code)
        label = short.get(code) or str(r.official_name)
        names[str(r.platform_abbr)] = label
        names.setdefault(code, label)
    return names


def pipeline_status() -> dict:
    txt = load_report("latest.md")
    first = txt.splitlines()[0] if txt else ""
    rec = load_report("recommendation_latest.md")
    gen = next((ln for ln in rec.splitlines() if ln.startswith("Generated")), "")
    dl = next((ln for ln in rec.splitlines() if ln.startswith("**Deadline")), "")
    return {"run_reason": first.replace("## ", ""), "generated": gen, "deadline": dl, "log": txt}
