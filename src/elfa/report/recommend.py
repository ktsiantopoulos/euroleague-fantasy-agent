"""Orchestrates projection + optimisation and renders the matchday recommendation."""
from __future__ import annotations

import json
import time
from pathlib import Path

import pandas as pd

from elfa.config import PROCESSED, RAW, ROOT
from elfa.features.dvp import attach_positions, compute_dvp, dvp_summary
from elfa.features.mapping import load_latest_market
from elfa.ingest.odds import fetch_odds, odds_dir
from elfa.model.optimise_bridge import run_optimiser
from elfa.model.projection import Params, project
from elfa.model.teams import load_schedule, team_ratings, upcoming_rounds


def _fmt_squad(sq: pd.DataFrame) -> str:
    cols = ["slot", "name", "pos", "team", "quotation", "md_pts", "md_p90", "why"]
    sq = sq.copy()
    slot_names = {"starter": "Starter", "sixth": "6th man", "bench": "Bench (50%)", "coach": "Coach"}
    sq["slot"] = sq.role.map(slot_names)
    sq["name"] = sq.apply(lambda r: f"**{r['name']}** (C)" if r.captain else r["name"], axis=1)
    sq["why"] = sq.apply(lambda r: (r["why"] + (f" · ⚠ {r['flags']}" if r["flags"] and r["flags"] != "coach" else "")), axis=1)
    sq = sq[cols].rename(columns={"quotation": "price", "md_pts": "exp pts", "md_p90": "p90", "why": "justification"})
    head = "| " + " | ".join(sq.columns) + " |\n|" + "---|" * len(sq.columns)
    body = "\n".join("| " + " | ".join(str(v) for v in row) + " |" for row in sq.itertuples(index=False))
    return head + "\n" + body


def _flags_section(proj: pd.DataFrame) -> str:
    fl = proj["flags"].astype(str).str.strip()
    f = proj[proj.in_roster & fl.ne("") & fl.ne("coach")]
    return "\n".join(f"- {r.name}: {r.flags}" for r in f.itertuples()) if len(f) else "- none"


def recommend(horizon_rounds: tuple[int, int, int] | None = None, mu_price: float = 0.0, params: Params | None = None,
              keep: list[str] | None = None) -> Path:
    md_number, market, cfg = load_latest_market()
    md_dir = RAW / "fantaking" / f"md_{md_number:02d}"
    roster = json.loads((md_dir / "roster.json").read_text(encoding="utf-8"))
    tmd = json.loads((md_dir / "team_matchday.json").read_text(encoding="utf-8"))
    roster_ids = {str(p["id"]) for p in roster["players"]}
    budget = float(tmd["credits"])
    trades_left = int(tmd["max_num_trades_per_matchday"]) - int(tmd.get("trades", 0))

    pg = pd.read_parquet(PROCESSED / "player_games.parquet")
    season = pg.season.max()
    pg = pg[pg.season == season]
    team_map = pd.read_csv(PROCESSED / "team_map.csv")
    player_map = pd.read_csv(PROCESSED / "player_map.csv", dtype={"platform_id": str, "person_code": str})
    schedule = load_schedule(season)

    pg = attach_positions(pg, player_map, market)
    dvp, _split = compute_dvp(pg)
    ratings = team_ratings(pg, schedule)

    n_rounds_now = int(cfg["current_matchday"].get("num_rounds") or 1)
    first = upcoming_rounds(schedule, n_rounds_now)
    start_next = (first[-1].round + 1) if first else None
    second = upcoming_rounds(schedule, 1, start_next) if start_next else []
    third = upcoming_rounds(schedule, 1, start_next + 1) if start_next else []
    horizon = [first, second, third]

    odds = fetch_odds(schedule, odds_dir())
    proj = project(market, roster_ids, pg, player_map, team_map, dvp, ratings, horizon, odds, params)
    proj.to_csv(PROCESSED / f"projection_md{md_number:02d}.csv", index=False)

    hold = run_optimiser(proj, budget, roster_ids, trades_left, mu_price, lock_squad=True)
    keep_ids = set()
    for k in keep or []:
        hit = proj[proj.name.str.lower().str.contains(k.lower())]
        keep_ids |= set(hit.platform_id)
    best = run_optimiser(proj, budget, roster_ids, trades_left, mu_price, lock_squad=False, keep_ids=keep_ids)

    rounds_txt = ", ".join(sorted({f"R{g.round}" for g in first}))
    lines = [
        f"# Recommendation — matchday {md_number} ({rounds_txt})",
        "",
        (f"Generated {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())} · team **{tmd['name']}** · budget {budget} · trades left {trades_left} · "
         f"odds {'ON (' + str(len(odds)) + ' games)' if odds else 'OFF (model margins)'}"),
        "",
        "## Decision",
        f"- Current squad, best lineup: **{hold.expected_md_pts} pts** expected this matchday.",
        f"- With trades: **{best.expected_md_pts} pts** expected (+{round(best.expected_md_pts - hold.expected_md_pts, 1)}), cost {best.cost}/{budget}.",
        f"- Trades: OUT {', '.join(best.trades_out) or '—'} → IN {', '.join(best.trades_in) or '—'}",
        f"- Captain **{best.captain}**, coach **{best.coach}**." + (f" Kept by request: {', '.join(keep)}." if keep else ""),
        "",
        "## Recommended squad (with trades)",
        _fmt_squad(best.squad),
        "",
        "## Current squad, best lineup (no trades)",
        _fmt_squad(hold.squad),
        "",
        "## Defence vs position (this season, shrunk to league mean; +PIR = concedes more)",
        "```",
        dvp_summary(dvp),
        "```",
        "",
        "## Top value outside the squad (exp pts per credit, players with a game this matchday)",
    ]
    cand = proj[(~proj.in_roster) & (proj.games_md > 0) & (proj.pos != "Head Coach")].sort_values("value", ascending=False)
    for pos_ in ("Guard", "Forward", "Center"):
        top = cand[cand.pos == pos_].head(5)
        lines.append(f"- {pos_}: " + "; ".join(f"{r.name} {r.team} {r.quotation} → {r.md_pts} ({r.flags or 'ok'})" for r in top.itertuples()))
    lines += [
        "",
        "## Flags",
        _flags_section(proj),
        "",
        "## Assumptions still to confirm",
        "- Coach: win by 21+ set to +25 (user-provided; not yet observed in API data).",
        "- Starting five constrained to 1–3 players per position (covers the platform's formations).",
        "- Price-change term inactive (μ = 0) until the price log has two or more matchdays.",
        f"- Optimiser status: {best.status} / {hold.status}.",
    ]
    out = ROOT / "reports" / f"recommendation_md{md_number:02d}.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    (ROOT / "reports" / "recommendation_latest.md").write_text("\n".join(lines), encoding="utf-8")
    return out
