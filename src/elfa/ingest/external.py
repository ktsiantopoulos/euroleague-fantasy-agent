"""External reference data and the season-start price log.

Fantasy Edge IQ (fantasyedgeiq.com) publishes a free CSV of all EuroLeague Fantasy players keyed by the
platform player id. We keep a slim copy (data/external/fantasyedge_players.csv) for two uses only:
  - `price_base`: the platform's season-start price per player, which the market no longer exposes;
  - a cross-source sanity check of our projection on the Model health page (their model leans on 2025-26
    data, so it is a divergence detector, not a benchmark).
Their matchup/FDR/projection numbers are never used by the model.

data/prices/price_base.csv is the season-start price per player. A value is written once and never
overwritten; sources in order of preference: fantasyedge price_base, our top-100 roster price at
matchday 1, the first price we ever saw for the player (marked as such).
"""
from __future__ import annotations

import io
import time

import pandas as pd
import requests

from elfa.config import DATA, PRICES, PROCESSED

FE_PLAYERS_URL = "https://www.fantasyedgeiq.com/euroleague-players-full.csv"
EXTERNAL = DATA / "external"
KEEP = ["player_id", "name", "team_abbr", "pos_short", "price", "price_base", "price_change", "proj_pir_est", "floor_est",
        "ceiling_est", "popularity_pct", "next5_fdr_1_easy_5_hard", "option_score_next5", "is_injured", "started_from_bench"]


def fetch_fantasyedge(timeout: int = 30) -> pd.DataFrame:
    """Download the players CSV; returns an empty frame (and prints why) when the site is unreachable."""
    try:
        r = requests.get(FE_PLAYERS_URL, timeout=timeout, headers={"User-Agent": "elfa/0.1 (personal fantasy tooling)"})
        r.raise_for_status()
        df = pd.read_csv(io.StringIO(r.text))
    except (requests.RequestException, pd.errors.ParserError, ValueError) as e:
        print(f"  ! fantasyedge: {type(e).__name__}: {str(e)[:100]}")
        return pd.DataFrame()
    cols = [c for c in KEEP if c in df.columns]
    out = df[cols].copy()
    out["player_id"] = pd.to_numeric(out.player_id, errors="coerce").astype("Int64")
    out = out.dropna(subset=["player_id"])
    out["pulled_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    EXTERNAL.mkdir(parents=True, exist_ok=True)
    out.to_csv(EXTERNAL / "fantasyedge_players.csv", index=False)
    print(f"  fantasyedge: {len(out)} players, {len(cols)} columns kept")
    return out


def load_fantasyedge() -> pd.DataFrame:
    fp = EXTERNAL / "fantasyedge_players.csv"
    return pd.read_csv(fp, dtype={"player_id": str}) if fp.exists() else pd.DataFrame()


def update_price_base(market: list[dict], md_number: int) -> pd.DataFrame:
    """Merge the season-start price log; existing values are never changed."""
    fp = PRICES / "price_base.csv"
    base = pd.read_csv(fp, dtype={"player_id": str}) if fp.exists() else pd.DataFrame(
        columns=["player_id", "first_name", "last_name", "price_base", "source", "seen_md"])
    have = set(base.player_id.astype(str))

    fe = load_fantasyedge()
    fe_base = dict(zip(fe.player_id.astype(str), fe.price_base)) if len(fe) and "price_base" in fe else {}
    top_fp = PROCESSED / "top_rosters.csv"
    top1: dict[str, float] = {}
    if top_fp.exists():
        t = pd.read_csv(top_fp, dtype={"player_id": str})
        t = t[t.matchday == t.matchday.min()]
        if len(t) and int(t.matchday.iloc[0]) == 1:
            top1 = t.groupby("player_id").quotation.first().to_dict()

    rows = []
    for m in market:
        pid = str(m["id"])
        if pid in have:
            continue
        if pid in fe_base and pd.notna(fe_base[pid]):
            val, src, seen = float(fe_base[pid]), "fantasyedge", 1
        elif pid in top1:
            val, src, seen = float(top1[pid]), "top100_md1", 1
        else:
            val, src, seen = float(m["quotation"]), "first_seen", md_number
        rows.append({"player_id": pid, "first_name": m.get("first_name", ""), "last_name": m.get("last_name", ""),
                     "price_base": val, "source": src, "seen_md": seen})
    if rows:
        base = pd.concat([base, pd.DataFrame(rows)], ignore_index=True)
    # a 'first_seen' value can be upgraded once a true season-start source appears
    for i, r in base[base.source == "first_seen"].iterrows():
        pid = str(r.player_id)
        if pid in fe_base and pd.notna(fe_base[pid]):
            base.loc[i, ["price_base", "source", "seen_md"]] = [float(fe_base[pid]), "fantasyedge", 1]
        elif pid in top1:
            base.loc[i, ["price_base", "source", "seen_md"]] = [float(top1[pid]), "top100_md1", 1]
    PRICES.mkdir(parents=True, exist_ok=True)
    base.to_csv(fp, index=False)
    return base


def load_price_base() -> pd.DataFrame:
    fp = PRICES / "price_base.csv"
    return pd.read_csv(fp, dtype={"player_id": str}) if fp.exists() else pd.DataFrame()
