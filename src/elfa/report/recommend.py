"""Orchestrates projection + optimisation and renders the matchday recommendation."""
from __future__ import annotations

import dataclasses
import datetime as dt
import json
import time
from pathlib import Path

import pandas as pd

from elfa.config import PROCESSED, RAW, ROOT
from elfa.features.dvp import attach_positions, compute_dvp, dvp_summary
from elfa.features.mapping import load_latest_market
from elfa.features.matchdays import matchday_turns
from elfa.ingest.odds import fetch_odds, odds_dir
from elfa.model.baseline import changes_between, trade_baseline
from elfa.model.inround import simulate
from elfa.model.optimise_bridge import run_optimiser
from elfa.model.projection import Params, project
from elfa.model.teams import (
    load_schedule,
    matchday_games,
    team_ratings,
    turns_from_market,
    upcoming_rounds,
)

ELITE_TILT = 0.04   # 4% at 100% top-100 ownership


def _fmt_squad(sq: pd.DataFrame) -> str:
    cols = ["slot", "name", "pos", "team", "quotation", "nights", "md_pts", "md_p90", "elite_own", "why"]
    sq = sq.copy()
    slot_names = {"starter": "Starter", "sixth": "6th man", "bench": "Bench (50%)", "coach": "Coach"}
    sq["slot"] = sq.role.map(slot_names)
    sq["nights"] = sq.games_json.map(lambda j: "/".join(f"T{g['turn']}" for g in json.loads(j)) if isinstance(j, str) else "")
    sq["name"] = sq.apply(lambda r: f"**{r['name']}** (C)" if r.captain else r["name"], axis=1)
    sq["why"] = sq.apply(lambda r: (r["why"] + (f" · ⚠ {r['flags']}" if r["flags"] and r["flags"] != "coach" else "")), axis=1)
    if "elite_own" not in sq:
        sq["elite_own"] = 0
    sq = sq[cols].rename(columns={"quotation": "price", "md_pts": "exp pts", "md_p90": "p90", "elite_own": "top100 own%", "why": "justification"})
    head = "| " + " | ".join(sq.columns) + " |\n|" + "---|" * len(sq.columns)
    body = "\n".join("| " + " | ".join(str(v) for v in row) + " |" for row in sq.itertuples(index=False))
    return head + "\n" + body


def _flags_section(proj: pd.DataFrame) -> str:
    fl = proj["flags"].astype(str).str.strip()
    f = proj[proj.in_roster & fl.ne("") & fl.ne("coach")]
    return "\n".join(f"- {r.name}: {r.flags}" for r in f.itertuples()) if len(f) else "- none"



def _stale_warning(md_number: int, first: list, cfg: dict) -> list[str]:
    """Banner lines when the matchday was rolled over from the schedule, or when its own round is already
    played and the fixtures fell back to the next round (a stale platform pull - do not act on it)."""
    out = []
    ro = cfg.get("rollover")
    if isinstance(ro, dict):
        out.append(f"> ℹ️ Platform still reported MD {ro['platform_current']} (finished); this report uses MD {ro['used']} "
                   f"with the deadline taken from the schedule ({ro['deadline_utc'][:16].replace('T', ' ')} UTC).")
    rounds = sorted({g.round for g in first})
    if rounds and rounds != [md_number]:
        out.append(f"> ⚠️ **Stale pull:** MD {md_number} is fully played, so the fixtures below are R{', R'.join(map(str, rounds))} "
                   f"but the squad, trades and deadline are still MD {md_number}'s. Re-run once the platform rolls over before acting.")
    try:
        h = json.loads((PROCESSED / "model_health.json").read_text(encoding="utf-8"))
        if h.get("drift"):
            out.append("> ⚠️ **Model drift:** " + "; ".join(h.get("reasons", [])) + " — weigh this recommendation with extra judgement.")
    except (OSError, ValueError):
        pass
    return out

def recommend(horizon_rounds: tuple[int, int, int] | None = None, mu_price: float = 0.0, params: Params | None = None,
              keep: list[str] | None = None) -> Path:
    md_number, market, cfg = load_latest_market()
    md_dir = RAW / "fantaking" / f"md_{md_number:02d}"
    roster = json.loads((md_dir / "roster.json").read_text(encoding="utf-8"))
    tmd = json.loads((md_dir / "team_matchday.json").read_text(encoding="utf-8"))
    roster_ids = {str(p["id"]) for p in roster["players"]}          # pending squad (what the platform shows now)
    budget = float(tmd["credits"])
    market_ids = {str(p["id"]) for p in market}
    base = trade_baseline(md_dir, tmd, cfg, market_ids)              # locked squad + full allowance while the window is open
    trades_left = base.trades_left
    print(f"  baseline: {base.label} ({len(base.ids)} ids), trades left {trades_left} - {base.note}")

    pg = pd.read_parquet(PROCESSED / "player_games.parquet")
    season = pg.season.max()
    pg = pg[pg.season == season]
    team_map = pd.read_csv(PROCESSED / "team_map.csv")
    player_map = pd.read_csv(PROCESSED / "player_map.csv", dtype={"platform_id": str, "person_code": str})
    schedule = load_schedule(season)

    pg = attach_positions(pg, player_map, market)
    dvp, _split = compute_dvp(pg)
    ratings = team_ratings(pg, schedule)

    # One fantasy matchday == one EuroLeague round. The platform's `num_rounds` is the number of game
    # nights (turns) inside the matchday — never use it to span several EuroLeague rounds.
    first = matchday_games(schedule, md_number)
    start_next = (first[-1].round + 1) if first else None
    second = upcoming_rounds(schedule, 1, start_next) if start_next else []
    third = upcoming_rounds(schedule, 1, start_next + 1) if start_next else []
    horizon = [first, second, third]
    turns = turns_from_market(market, team_map)
    n_turns = int(cfg["current_matchday"].get("num_rounds") or 0)
    if n_turns and turns and max(turns.values()) != n_turns:
        print(f"  ! platform says {n_turns} game night(s) but the market's round numbers go up to {max(turns.values())}")

    odds = fetch_odds(schedule, odds_dir())
    proj = project(market, roster_ids, pg, player_map, team_map, dvp, ratings, horizon, odds, params, turns=turns)
    own_fp = PROCESSED / "top_ownership.csv"
    if own_fp.exists():
        own = pd.read_csv(own_fp)
        proj["elite_own"] = proj.name.map(dict(zip(own.player, own.own_pct))).fillna(0).astype(int)
    else:
        proj["elite_own"] = 0
    # consensus prior from managers who demonstrably beat the market: up to +ELITE_TILT at 100% ownership
    proj["md_pts_model"] = proj.md_pts
    tilt = 1 + ELITE_TILT * proj.elite_own / 100.0
    proj["md_pts"] = (proj.md_pts * tilt).round(2)
    proj["horizon_pts"] = (proj.horizon_pts * tilt).round(2)
    proj["md_p90"] = (proj.md_p90 * tilt).round(2)
    proj.to_csv(PROCESSED / f"projection_md{md_number:02d}.csv", index=False)

    # hold = the squad the optimiser trades away from (locked squad while the window is open), best lineup, no trades
    hold = run_optimiser(proj, budget, base.ids, trades_left, mu_price, lock_squad=True)
    # pending = what is selected on the platform right now (differs from hold only while trades are pending)
    pending = run_optimiser(proj, budget, roster_ids, 0, mu_price, lock_squad=True) if roster_ids != base.ids else hold
    keep_ids = set()
    for k in keep or []:
        hit = proj[proj.name.str.lower().str.contains(k.lower())]
        keep_ids |= set(hit.platform_id)
    best = run_optimiser(proj, budget, base.ids, trades_left, mu_price, lock_squad=False, keep_ids=keep_ids)
    # what to change on the platform to get from the pending squad to the recommended one
    best_ids = set(best.squad.platform_id)
    undo_ids, add_ids = changes_between(roster_ids, best_ids)
    names = dict(zip(proj.platform_id, proj.name))
    to_undo = [names.get(i, i) for i in sorted(undo_ids)]
    to_add = [names.get(i, i) for i in sorted(add_ids)]

    rounds_txt = ", ".join(sorted({f"R{g.round}" for g in first}))
    deadline = (cfg.get("current_round") or {}).get("started_at", "")[:16].replace("T", " ") + " UTC" if cfg.get("current_round") else "unknown"
    # night dates in turn order: T1 = earliest date of the games the platform puts in sub-round 1, etc.
    by_turn: dict[int, str] = {}
    for g in first:
        t = turns.get(g.home) or turns.get(g.away)
        if t:
            by_turn[t] = min(by_turn.get(t, g.date_utc[:10]), g.date_utc[:10])
    nights = [by_turn[t] for t in sorted(by_turn)] if by_turn else sorted({g.date_utc[:10] for g in first})
    _rounds_tbl, nights_tbl = matchday_turns(md_number)
    if nights_tbl and nights_tbl != nights:
        print(f"  ! matchdays.csv nights {nights_tbl} differ from the market's {nights} - using the market")
    nights_txt = ", ".join(f"T{i + 1}={d[5:]}" for i, d in enumerate(nights))
    plan_best = simulate(best.squad)
    plan_hold = simulate(hold.squad)
    lines = [
        f"# Recommendation — matchday {md_number} ({rounds_txt})",
        "",
        f"**Deadline: {deadline}** (first tip-off of the matchday; trades close then).",
        "",
        (f"Generated {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())} · team **{tmd['name']}** · budget {budget} · "
         f"trades {trades_left} vs the {base.label} ({base.pending_trades} pending on the platform) · "
         f"odds {'ON (' + str(len(odds)) + ' games)' if odds else 'OFF (model margins)'}"),
        f"_{base.note}_",
    ] + _stale_warning(md_number, first, cfg) + [
        "",
        "## Decision",
        f"- Game nights: {nights_txt}. Bench players with later nights are swap options; captain can move to a not-yet-played starter.",
        f"- {base.label.capitalize()}, best lineup: **{hold.expected_md_pts} pts** expected; in-round swaps add {plan_hold.gain:+.1f} (simulated).",
    ] + ([f"- Pending squad (your {base.pending_trades} current trade(s)), best lineup: **{pending.expected_md_pts} pts** expected "
          f"({pending.expected_md_pts - hold.expected_md_pts:+.1f} vs the locked squad)."] if pending is not hold else []) + [
        f"- Recommended with ≤{trades_left} trade(s): **{best.expected_md_pts} pts** expected (+{round(best.expected_md_pts - hold.expected_md_pts, 1)} vs {base.label}"
        + (f", {best.expected_md_pts - pending.expected_md_pts:+.1f} vs pending" if pending is not hold else "")
        + f"); in-round swaps add {plan_best.gain:+.1f} (simulated); cost {best.cost}/{budget}.",
        f"- Trades vs the {base.label}: OUT {', '.join(best.trades_out) or '—'} → IN {', '.join(best.trades_in) or '—'}",
    ] + ([f"- **To do on the platform** (from what you have selected now): remove {', '.join(to_undo) or '—'} → add {', '.join(to_add) or '—'}"
          if (to_undo or to_add) else "- **Nothing to change on the platform** — your pending squad is already the recommendation."]
         if base.open else []) + [
        f"- Captain **{best.captain}**, coach **{best.coach}**." + (f" Kept by request: {', '.join(keep)}." if keep else ""),
        "",
        "## Recommended squad (with trades)",
        _fmt_squad(best.squad),
        "",
        "### In-round plan (from 3,000 simulations)",
        "- " + ("\n- ".join(plan_best.notes) if plan_best.notes else "no frequent swaps — the lineup is mostly set-and-forget"),
        "- Rule of thumb after each night: promote a not-yet-played bench player over a field player of the same position whose realised score is below the bench player's expectation; move the captaincy to the not-yet-played starter with the highest expectation if it beats the captain's realised total.",
        "",
        f"## {base.label.capitalize()}, best lineup (no trades)",
        _fmt_squad(hold.squad),
    ] + (["", f"## Pending squad on the platform ({base.pending_trades} trade(s) made, reversible), best lineup",
          _fmt_squad(pending.squad)] if pending is not hold else []) + [
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
        lines.append(f"- {pos_}: " + "; ".join(f"{r.name} {r.team} {r.quotation} → {r.md_pts} (top100 {r.elite_own}%{', ' + r.flags if r.flags else ''})" for r in top.itertuples()))
    lines += [
        "",
        "## Flags",
        _flags_section(proj),
        "",
        "## Assumptions still to confirm",
        "- Coach: win by 21+ set to +25 (user-provided; not yet observed in API data).",
        "- Starting five constrained to 1–3 players per position (covers the platform's formations).",
        "- Price-change term inactive (μ = 0) until the price log has two or more matchdays.",
        "- Elite-consensus tilt: expected points scaled by up to +4% at 100% top-100 ownership (raw model value kept as md_pts_model).",
        "- Soft rules from the top-100 study: 3 points penalty per player above 3 from one club; 1 point per credit for bench players under 6.0.",
        f"- Optimiser status: {best.status} / {hold.status}.",
    ]
    out = ROOT / "reports" / f"recommendation_md{md_number:02d}.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    (ROOT / "reports" / "recommendation_latest.md").write_text("\n".join(lines), encoding="utf-8")

    # structured copy for the dashboard
    def _records(sq: pd.DataFrame) -> list[dict]:
        cols = ["role", "name", "pos", "team", "quotation", "md_pts", "md_p90", "md_sd", "elite_own", "why", "flags", "captain", "first_turn", "games_json"]
        return [{k: (None if pd.isna(v) else (v.item() if hasattr(v, "item") else v)) for k, v in r.items()} for r in sq[[c for c in cols if c in sq]].to_dict("records")]

    def _pl(names: list[str]) -> list[dict]:
        rows = []
        for n in names:
            hit = proj[proj.name == n]
            if len(hit):
                r = hit.iloc[0]
                rows.append({"name": n, "pos": r.pos, "team": r.team, "price": float(r.quotation), "md_pts": float(r.md_pts)})
            else:
                rows.append({"name": n})
        return rows

    top_value = {}
    for pos_ in ("Guard", "Forward", "Center"):
        top_value[pos_] = [{"name": r.name, "team": r.team, "price": r.quotation, "md_pts": r.md_pts, "elite_own": int(r.elite_own), "flags": r.flags or ""}
                           for r in cand[cand.pos == pos_].head(5).itertuples()]
    payload = {
        "matchday": md_number, "rounds": sorted({g.round for g in first}), "deadline_utc": (cfg.get("current_round") or {}).get("started_at"),
        "nights": nights, "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "team": tmd["name"], "budget": budget,
        "trades_left": trades_left, "odds_games": len(odds), "kept": keep or [],
        "baseline": {"label": base.label, "open": base.open, "note": base.note, "max_trades": base.max_trades,
                     "pending_trades": base.pending_trades, "locked_known": bool(base.locked_ids)},
        "pending": {"expected": pending.expected_md_pts, "cost": pending.cost, "status": pending.status, "captain": pending.captain,
                    "coach": pending.coach, "squad": _records(pending.squad), "differs": pending is not hold},
        "changes_vs_pending": {"remove": _pl(to_undo), "add": _pl(to_add)},
        "hold": {"expected": hold.expected_md_pts, "inround_gain": round(plan_hold.gain, 1), "cost": hold.cost, "status": hold.status, "captain": hold.captain, "coach": hold.coach, "squad": _records(hold.squad)},
        "best": {"expected": best.expected_md_pts, "inround_gain": round(plan_best.gain, 1), "cost": best.cost, "status": best.status, "captain": best.captain, "coach": best.coach,
                 "trades_out": _pl(best.trades_out), "trades_in": _pl(best.trades_in), "squad": _records(best.squad), "plan": plan_best.notes},
        "top_value": top_value,
        "flags": [{"name": r.name, "flags": r.flags} for r in proj[proj.in_roster & proj["flags"].astype(str).str.strip().ne("") & proj["flags"].astype(str).ne("coach")].itertuples()],
    }
    (ROOT / "reports" / f"recommendation_md{md_number:02d}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    (ROOT / "reports" / "recommendation_latest.json").write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    froze = freeze_if_pre_lock(md_number, proj, first, base, hold, best, budget, trades_left, params=params)
    print(f"  lock snapshot: {froze}")
    return out


def matchday_lock_utc(first: list) -> dt.datetime | None:
    """Trades lock at the first tip-off of the matchday (one minute before, the platform's convention)."""
    if not first:
        return None
    tip = min(dt.datetime.fromisoformat(g.date_utc.replace("Z", "+00:00")) for g in first)
    tip = tip if tip.tzinfo else tip.replace(tzinfo=dt.UTC)
    return tip - dt.timedelta(minutes=1)


def _squad_records(sol) -> list[dict]:
    sq = sol.squad
    return [{"platform_id": str(r.platform_id), "name": r.name, "pos": r.pos, "role": r.role, "captain": bool(r.captain),
             "md_pts": float(r.md_pts), "md_sd": float(r.md_sd)} for r in sq.itertuples()]


def freeze_if_pre_lock(md_number: int, proj: pd.DataFrame, first: list, base, hold, best, budget: float, trades_left: int,
                       now: dt.datetime | None = None, params: Params | None = None) -> str:
    """Keep the last projection made BEFORE the matchday locks - the only honest thing to score afterwards.

    Every pre-lock run overwrites projection_mdXX_locked.csv / decision_mdXX_locked.json; runs after the lock
    never touch them, so post-lock data (first-night box scores, stale pulls) can't leak into the evaluation.
    """
    now = now or dt.datetime.now(dt.UTC)
    lock = matchday_lock_utc(first)
    rounds = sorted({g.round for g in first})
    if lock is None or rounds != [md_number]:
        return "skipped (fixtures are not this matchday's own round)"
    if not base.open or now >= lock:
        return f"kept (matchday locked at {lock:%Y-%m-%d %H:%M} UTC)"
    proj.to_csv(PROCESSED / f"projection_md{md_number:02d}_locked.csv", index=False)
    decision = {
        "matchday": md_number, "frozen_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "lock_utc": lock.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "budget": budget, "trades_left": trades_left, "baseline_ids": sorted(base.ids),
        "hold": {"expected": float(hold.expected_md_pts), "captain": hold.captain, "squad": _squad_records(hold)},
        "best": {"expected": float(best.expected_md_pts), "captain": best.captain, "squad": _squad_records(best),
                 "trades_out": best.trades_out, "trades_in": best.trades_in},
        "params": dataclasses.asdict(params or Params.load()),
    }
    (PROCESSED / f"decision_md{md_number:02d}_locked.json").write_text(json.dumps(decision, indent=1, default=str), encoding="utf-8")
    return f"written (locks {lock:%Y-%m-%d %H:%M} UTC)"
