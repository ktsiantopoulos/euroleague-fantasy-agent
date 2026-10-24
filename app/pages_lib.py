"""Shared page renderers for the two Streamlit apps.

mode = "team"  : the private app — all reports plus everything about my own squad.
mode = "scout" : the public scouting app — only league-wide reports (players, teams, market);
                 nothing about my team is loaded or shown.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

import altair as alt
import pandas as pd
import streamlit as st

_ROOT = Path(__file__).resolve().parents[1]
for _p in (str(_ROOT), str(_ROOT / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from app import data as D
from app import theme as TH

SLOT = {"starter": "Starter", "sixth": "6th man", "bench": "Bench (50%)", "coach": "Coach"}

TEAM_PAGES = ["Recommendation", "What-if optimiser"]
SCOUT_PAGES = ["Overview", "Projections", "Captain", "Fixtures & schedule", "Game script (odds)", "Defence vs position",
               "Team context", "Player", "Top 100 managers", "Market & prices", "Model health"]
ATHENS = ZoneInfo("Europe/Athens")

# Column titles with explanations (hover the header)
COL = {
    "slot": st.column_config.TextColumn("Slot", help="Starters, 6th man and coach score 100%; bench scores 50%. Captain (C) scores 200%."),
    "player": st.column_config.TextColumn("Player"),
    "name": st.column_config.TextColumn("Player"),
    "pos": st.column_config.TextColumn("Pos", help="Fantasy position: Guard / Forward / Center / Head Coach"),
    "team": st.column_config.TextColumn("Team"),
    "club": st.column_config.TextColumn("Club"),
    "price": st.column_config.NumberColumn("Price", help="Current credits on the platform", format="%.1f"),
    "quotation": st.column_config.NumberColumn("Price", help="Current credits on the platform", format="%.1f"),
    "nights": st.column_config.TextColumn("Nights", help="Game nights of this matchday the player plays (T1 = first night). Later-night bench players can be promoted after earlier nights."),
    "prob_play": st.column_config.NumberColumn("P(play)", help="Platform availability: 1.0 = fit, lower = doubtful; expected points are multiplied by it", format="%.2f"),
    "min": st.column_config.NumberColumn("Min", help="Projected minutes per game: 20% last game, 30% last-3 mean, 50% last-5 mean, discounted for tiny samples", format="%.0f"),
    "min_hat": st.column_config.NumberColumn("Min", help="Projected minutes per game: 20% last game, 30% last-3 mean, 50% last-5 mean, discounted for tiny samples", format="%.0f"),
    "PIR/min": st.column_config.NumberColumn("PIR/min", help="Projected PIR per minute: 60% last-5 games, 40% season, shrunk toward the league average", format="%.2f"),
    "rate_hat": st.column_config.NumberColumn("PIR/min", help="Projected PIR per minute: 60% last-5 games, 40% season, shrunk toward the league average", format="%.2f"),
    "exp": st.column_config.NumberColumn("Exp pts", help="Expected fantasy points this matchday: all games summed, PIR + 10% win bonus, home/away, pace and DvP adjustments, elite-consensus tilt", format="%.1f"),
    "md_pts": st.column_config.NumberColumn("Exp pts", help="Expected fantasy points this matchday: all games summed, PIR + 10% win bonus, home/away, pace and DvP adjustments, elite-consensus tilt", format="%.1f"),
    "p90": st.column_config.NumberColumn("p90", help="90th-percentile outcome — the ceiling. Used for captain choice.", format="%.1f"),
    "md_p90": st.column_config.NumberColumn("p90", help="90th-percentile outcome — the ceiling. Used for captain choice.", format="%.1f"),
    "md_sd": st.column_config.NumberColumn("±", help="Uncertainty (standard deviation) of the matchday projection", format="%.1f"),
    "value": st.column_config.NumberColumn("Pts/credit", help="Expected points per credit of price", format="%.2f"),
    "horizon_pts": st.column_config.NumberColumn("3-wk value", help="Weighted expected points over this matchday and the next two (1.0 / 0.6 / 0.3)", format="%.1f"),
    "popularity": st.column_config.NumberColumn("Global own", help="Share of all managers owning the player", format="%.0f%%"),
    "elite_own": st.column_config.NumberColumn("Top-100 own", help="Share of the top-100 managers owning the player (last played matchday)", format="%d%%"),
    "in_roster": st.column_config.CheckboxColumn("Mine", help="Currently in your squad"),
    "flags": st.column_config.TextColumn("Flags", help="Data warnings: few games, DNP last game, no game this matchday"),
    "justification": st.column_config.TextColumn("Why", help="Minutes × rate, then each game: night, opponent, DvP tilt, win probability → points", width="large"),
    "why": st.column_config.TextColumn("Why", help="Minutes × rate, then each game: night, opponent, DvP tilt, win probability → points", width="large"),
    "games_md": st.column_config.NumberColumn("G", help="Games this matchday"),
    # captain page
    "floor": st.column_config.NumberColumn("Floor (p10)", help="10th-percentile outcome — what a bad night looks like. Sort by this for a safe captain.", format="%.1f"),
    "games_txt": st.column_config.TextColumn("Games (exp pts, win %)", help="Each game this matchday: night, opponent, expected points and the team's win probability", width="large"),
    "elite_cap": st.column_config.NumberColumn("Top-100 C", help="How many of the top-100 managers captained him in the last played matchday"),
    "elite_cap_mds": st.column_config.NumberColumn("C in MDs", help="Number of matchdays this season in which at least one top-100 manager captained him"),
    "captain_now": st.column_config.CheckboxColumn("Your C", help="Your current captain on the platform"),
    "shot_share": st.column_config.NumberColumn("Shot %", help="Share of the team's field-goal attempts per game (player FGA/G ÷ team FGA/G)", format="%.1f%%"),
    "fga_per_min": st.column_config.NumberColumn("FGA/min", help="Field-goal attempts per minute played — usage rate", format="%.2f"),
    "usage_delta": st.column_config.NumberColumn("Δ usage", help="FGA per minute over the last 3 games minus the season rate (+ = taking more shots lately)", format="%+.2f"),
    "min_delta": st.column_config.NumberColumn("Δ min", help="Minutes per game over the last 3 games minus the season average", format="%+.1f"),
    "role_signal": st.column_config.TextColumn("Role", help="rising = more shots per minute AND more minutes in the last 3 games; falling = the reverse"),
    "fd_pg": st.column_config.NumberColumn("FD", help="Fouls drawn per game (+1 PIR each)", format="%.1f"),
    "blka_pg": st.column_config.NumberColumn("BLKA", help="Shots blocked per game (−1 PIR each)", format="%.1f"),
    "price_base": st.column_config.NumberColumn("Start price", help="Season-start price (Fantasy Edge IQ price_base, or our top-100 roster price at matchday 1, or the first price we saw)", format="%.1f"),
    "price_delta": st.column_config.NumberColumn("Δ since start", help="Current price minus season-start price — how much of the player's value has already been priced in", format="%+.1f"),
    "starter_last": st.column_config.CheckboxColumn("Started", help="Started the team's last game (official box score)"),
    "risk": st.column_config.TextColumn("Risk", help="doubtful = platform availability < 1; DNP last = did not play last game; few games = under 3 games; usage rising / falling = role signal"),
    "fdr": st.column_config.NumberColumn("FDR", help="Fixture difficulty 1 (easy) – 5 (hard): opponent's PIR/points/FGA/rebounds allowed and pace, ± venue, ± win probability", format="%.1f"),
    "next_n_avg": st.column_config.NumberColumn("Next-5 FDR", help="Average fixture difficulty over the club's next five games (1 easy – 5 hard)", format="%.2f"),
    "matchup_ease": st.column_config.NumberColumn("Ease", help="0–100: how easy it is to score fantasy points against this club (100 = easiest)", format="%.0f"),
    "defence_weakness_score": st.column_config.NumberColumn("Def. weakness", help="Average percentile of PIR, points, FGA and rebounds allowed (100 = leaks the most)", format="%.0f"),
    "pace": st.column_config.NumberColumn("Pace", help="Possessions per game (FGA + 0.44·FTA − OREB + TOV, averaged with the opponents' possessions)", format="%.1f"),
    "trap": st.column_config.NumberColumn("Trap score", help="Global ownership percentile minus expected-points percentile — high = popular but projected low", format="%.0f"),
    # fixtures / odds pages
    "night": st.column_config.TextColumn("Night", help="Game night of the matchday (T1 = first). In-round swaps are allowed between nights."),
    "local": st.column_config.TextColumn("Tip-off (Athens)", help="Local time in Athens"),
    "home": st.column_config.TextColumn("Home"),
    "away": st.column_config.TextColumn("Away"),
    "favourite": st.column_config.TextColumn("Favourite", help="Bookmaker favourite and its win probability (vig removed, consensus across books)"),
    "home_win": st.column_config.NumberColumn("Home win %", help="Consensus implied probability that the home team wins", format="%d%%"),
    "spread": st.column_config.NumberColumn("Spread", help="Consensus handicap for the home team (negative = home favourite). The projection uses −spread as the expected margin.", format="%+.1f"),
    "total": st.column_config.NumberColumn("Total", help="Consensus over/under points line — a pace and scoring-environment signal", format="%.1f"),
    "books": st.column_config.NumberColumn("Books", help="Bookmakers quoting the game"),
    "blowout": st.column_config.TextColumn("Blowout risk", help="|spread| ≥ 12 high, ≥ 8 medium. In a blowout the favourite's starters sit the fourth quarter — fewer minutes, lower PIR."),
    "scoring_env": st.column_config.TextColumn("Scoring env.", help="Total vs the median total of the matchday: fast (≥ +4), slow (≤ −4), average"),
    "d_win": st.column_config.NumberColumn("Δ win pp", help="Change in home win probability since the first odds snapshot (percentage points)", format="%+.1f"),
    "d_spread": st.column_config.NumberColumn("Δ spread", help="Change in the home spread since the first snapshot", format="%+.1f"),
    "d_total": st.column_config.NumberColumn("Δ total", help="Change in the total since the first snapshot", format="%+.1f"),
    "games_md_team": st.column_config.NumberColumn("G this MD", help="Games the club plays in this matchday (one per round; two only in a genuine double round)"),
    "games_h": st.column_config.NumberColumn("G horizon", help="Games the club plays in the selected horizon"),
    "home_h": st.column_config.NumberColumn("Home", help="Home games in the horizon"),
    "rest": st.column_config.NumberColumn("Rest days", help="Days between the club's last game and its first game of this matchday"),
    "gap": st.column_config.NumberColumn("Min gap", help="Shortest gap in days between consecutive games in the horizon (1 = back-to-back)"),
}

DVP_COL = {
    "DvP": st.column_config.NumberColumn("DvP", help="PIR over expectation the opponent concedes to this position per game (+ = weak defence)", format="%+.1f"),
    "rank": st.column_config.NumberColumn("Rank", help="1 = weakest defence in the league at this position, 20 = strongest"),
    "games": st.column_config.NumberColumn("n", help="Games the opponent has played — sample size"),
    "win %": st.column_config.NumberColumn("Win %", help="Probability this team wins the game (bookmakers when available) — the 10% bonus", format="%d%%"),
    "best options": st.column_config.TextColumn("Best options", help="Top three players of that team and position by expected points (price, expected)", width="large"),
}


def show(df: pd.DataFrame, **kw):
    cfg = {c: COL[c] for c in df.columns if c in COL}
    st.dataframe(df, column_config=cfg, width="stretch", hide_index=True, **kw)


# ------------------------------------------------------------------------------------------ cached loaders
@st.cache_data(ttl=600)
def proj_data():
    return D.load_projection()


@st.cache_data(ttl=600)
def player_games():
    return D.load_player_games()


@st.cache_data(ttl=600)
def csv(name):
    return D.load_csv(name)


@st.cache_data(ttl=600)
def prices():
    return D.load_prices()


@st.cache_data(ttl=600)
def roster_state():
    return D.load_roster_state()


def scrub_team(text: str) -> str:
    """Remove anything that identifies my team from a status line (used by the scouting app)."""
    text = re.sub(r"·\s*team \*\*.*?\*\*\s*·\s*budget [\d.]+\s*·\s*trades left \d+\s*·", "·", text)
    return re.sub(r"\s{2,}", " ", text).strip()


@st.cache_data(ttl=600)
def rec_json():
    return D.load_recommendation()


@st.cache_data(ttl=600)
def schedule_df():
    return D.load_schedule_df()


@st.cache_data(ttl=600)
def odds_df():
    return D.load_odds_snapshots()


def current_rounds_and_nights(sched: pd.DataFrame) -> tuple[list[int], list[str]]:
    """Rounds and game-night dates (UTC, YYYY-MM-DD) of the matchday the dashboard is showing.

    From the committed matchday calendar (data/processed/matchdays.csv, built by `elfa build`), then the
    recommendation JSON, then the schedule (the matchday's own round, or the next unplayed one).
    """
    matchday_turns = D.elfa_attr("elfa.features.matchdays", "matchday_turns")
    rounds, nights = matchday_turns(D.latest_matchday(), csv("matchdays.csv"))
    rec = rec_json()
    if not rounds and rec.get("rounds"):
        rounds = [int(r) for r in rec["rounds"]]
        nights = list(rec.get("nights") or [])
    if not rounds and len(sched):
        # one fantasy matchday == one EuroLeague round; fall back to the next unplayed round if that one is over
        md = D.latest_matchday()
        if md and (~sched[sched["round"] == md].played).any():
            rounds = [md]
        else:
            nxt = sched[~sched.played]["round"]
            rounds = [int(nxt.min())] if len(nxt) else []
    if rounds and not nights and len(sched):
        nights = sorted(sched[sched["round"].isin(rounds)].date_utc.dt.strftime("%Y-%m-%d").unique().tolist())
    return rounds, nights


def _local(ts: pd.Timestamp) -> str:
    ts = pd.Timestamp(ts)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    return ts.tz_convert(ATHENS).strftime("%a %d %b %H:%M")


def _latest_odds() -> pd.DataFrame:
    od = odds_df()
    if od.empty:
        return od
    return od[od.snapshot == od.snapshot.max()].copy()


def header(mode: str, md: int):
    status = D.pipeline_status()
    rec = rec_json()
    deadline = rec.get("deadline_utc")
    if mode == "team":
        tmd, _roster = roster_state()
        TH.md(TH.header("Fantasy Agent", f"{tmd.get('name', '')}  ·  matchday {md or '—'}", deadline))
        trades_left = f"{int(tmd.get('max_num_trades_per_matchday', 0)) - int(tmd.get('trades', 0))}" if tmd else "—"
        items = [("Credits", str(tmd.get("credits", "—")), "", "text"), ("Trades left", trades_left, "of 4 · coach counts", "text"),
                 ("Total pts", str(tmd.get("total_pts", "—")), "", "text")]
        if rec:
            h, b = rec["hold"], rec["best"]
            items += [("Current squad", f"{h['expected']:.1f}", "best lineup, no trades", "muted"),
                      ("With trades", f"{b['expected']:.1f}", f"▲ +{b['expected'] - h['expected']:.1f} expected", "pos"),
                      ("Managed in-round", f"{b['inround_gain']:+.1f}", "swaps & captain moves, simulated", "gold")]
        TH.md(TH.kpis(items))
        st.caption(f"{status['generated']}  ·  last run: {status['run_reason']}")
    else:
        TH.md(TH.header("Fantasy Scout", f"matchday {md or '—'}  ·  league-wide analytics", deadline, mark="ELS"))
        st.caption("League-wide projections, matchup analytics, elite-manager tendencies and market data for the EuroLeague Fantasy Challenge. "
                   "Scoring: PIR + 10% if the team wins; starters 100%, bench 50%, captain ×2.  ·  " + scrub_team(status["generated"]))


# ------------------------------------------------------------------------------------------ team pages
def _squad_table(sq: pd.DataFrame) -> pd.DataFrame:
    sq = sq.copy()
    sq["slot"] = sq.role.map(SLOT)
    sq["player"] = sq.apply(lambda r: f"{r['name']} (C)" if r.captain else r["name"], axis=1)
    cols = ["slot", "player", "pos", "team", "quotation", "nights", "md_pts", "md_p90", "why"]
    return sq[cols].rename(columns={"quotation": "price", "md_pts": "exp", "md_p90": "p90", "why": "justification"})


def page_recommendation(proj: pd.DataFrame, md: int):
    rec = rec_json()
    if not rec:
        st.markdown(D.load_report("recommendation_latest.md"))
        return
    b, h = rec["best"], rec["hold"]
    rounds = " + ".join(f"R{r}" for r in rec.get("rounds", []))
    nights = " · ".join(f"T{i + 1} = {d[5:]}" for i, d in enumerate(rec.get("nights", [])))
    odds = TH.chip(f"ODDS ON · {rec['odds_games']} GAMES", "pos") if rec.get("odds_games") else TH.chip("ODDS OFF · MODEL MARGINS", "neg")
    TH.md(f'<div class="elf-h1">Matchday {rec["matchday"]}</div><div class="elf-sub" style="margin-bottom:10px">{rounds} · {len(rec.get("nights", []))} night(s) · {nights} &nbsp; {odds}</div>')
    kept = f" · kept by request: {', '.join(rec['kept'])}" if rec.get("kept") else ""
    TH.md(TH.trades(b["trades_out"], b["trades_in"], f"Cost {b['cost']} / {rec['budget']}  ·  Captain {b['captain'].upper()}  ·  Coach {b['coach'].upper()}  ·  {b['status']}{kept}"))
    st.write("")
    left, right = st.columns([2.2, 1])
    with left:
        multi = len(rec.get("nights", [])) > 1
        badges = [TH.chip("NIGHT BALANCE " + ("RELAXED" if "relaxed" in b["status"] else "OK"), "gold" if "relaxed" in b["status"] else "pos")] if multi else []
        TH.md(TH.lineup_board(b["squad"], "Recommended squad", badges))
        with st.expander("Current squad, best lineup (no trades)"):
            TH.md(TH.lineup_board(h["squad"], f"Current squad · {h['expected']:.1f} pts"))
    with right:
        plan = [("AFTER T1", n) for n in b.get("plan", [])] or [("INFO", "no frequent swaps — the lineup is mostly set-and-forget")]
        plan.append(("RULE", "After each night: promote a not-yet-played bench player over a same-position field player whose realised score is below the bench expectation; move the captaincy to the best not-yet-played starter if it beats the captain's realised total."))
        TH.md(TH.notes(f"In-round plan · simulated gain {b['inround_gain']:+.1f}", plan))
        st.write("")
        rows = dvp_targets(proj)
        TH.md(TH.target_rows("Who to target · this matchday", rows[rows.DvP >= 1.0].head(6).to_dict("records") if len(rows) else []))
        st.write("")
        tv = rec.get("top_value", {})
        items = [(p[0], ", ".join(f"{r['name']} {r['price']} → {r['md_pts']:.0f}" for r in tv.get(p, [])[:4])) for p in ("Guard", "Forward", "Center")]
        TH.md(TH.notes("Top value outside the squad", items, "info"))
        if rec.get("flags"):
            TH.md(TH.notes("Flags", [("⚠", f"{f['name']}: {f['flags']}") for f in rec["flags"]], "gold"))
    sc = sell_candidates(proj)
    if len(sc):
        st.markdown("**Sell candidates in your squad** — low 3-week value per credit, price already up, hard run of fixtures")
        st.dataframe(sc, width="stretch", hide_index=True, column_config={
            **{c: COL[c] for c in sc.columns if c in COL},
            "sell": st.column_config.NumberColumn("Sell score", help="0–100 rank blend: 50% low 3-week points per credit, 25% price gain since start, 25% hard next-5", format="%.0f"),
            "why_sell": st.column_config.TextColumn("Why", width="large")})
    tr = traps(proj)
    if len(tr):
        st.markdown("**Traps — popular but projected low** (don't buy the crowd's picks on name alone)")
        show(tr)
    TH.md('<div class="elf-foot">Model: minutes × PIR rate × home/pace/DvP, +10% win bonus (bookmaker odds when available) · elite tilt +4% at 100% top-100 ownership · soft club cap 3 · bench price floor 6.0</div>')
    with st.expander("Full text report"):
        st.markdown(D.load_report("recommendation_latest.md"))


def page_whatif(proj: pd.DataFrame):
    tmd, roster = roster_state()
    roster_ids = {str(p["id"]) for p in roster.get("players", [])}
    st.subheader("Run the optimiser with your constraints")
    if proj.empty:
        st.warning("No projection yet.")
        return
    simulate = D.elfa_attr("elfa.model.inround", "simulate")
    optimise = D.elfa_attr("elfa.optimise.lineup", "optimise")

    names = sorted(proj.name.tolist())
    in_squad = sorted(proj[proj.in_roster].name.tolist())
    colA, colB = st.columns(2)
    keep = colA.multiselect("Must keep", in_squad)
    exclude = colB.multiselect("Exclude from consideration", names)
    colC, colD, colE, colF = st.columns(4)
    trades = colC.slider("Max trades", 0, 4, int(tmd.get("max_num_trades_per_matchday", 4)) - int(tmd.get("trades", 0)) if tmd else 4)
    budget = colD.number_input("Budget", value=float(tmd.get("credits", 100.0)), step=0.1)
    balance = colE.checkbox("Night balance rule", value=True,
                            help="On multi-night matchdays keep ≥3 field players on night 1 and ≥2 bench players with later games, so you can react after the first night.")
    RISK = {"Balanced": 0.0, "Safe": 0.35, "Aggressive": -0.15}
    mode_r = colF.selectbox("Risk mode", list(RISK), help="Objective = expected pts − λ × uncertainty. Safe (λ = 0.35) prefers steady players — use it for nights you cannot react to; "
                            "Aggressive (λ = −0.15) rewards variance — use it when chasing a rank. Balanced is the model's plain expectation.")
    lam = RISK[mode_r]
    if st.button("Optimise", type="primary"):
        df = proj[~proj.name.isin(exclude)].copy()
        if lam:
            df["md_pts"] = (df.md_pts - lam * df.md_sd).clip(lower=0)
            df["horizon_pts"] = (df.horizon_pts - lam * df.md_sd).clip(lower=0)
        keep_ids = set(df[df.name.isin(keep)].platform_id)
        with st.spinner("solving…"):
            sol = optimise(df, budget, roster_ids, max_trades=trades, keep_ids=keep_ids, balance=balance)
            if lam:  # re-score the chosen squad on the plain expectation so the numbers stay comparable
                sol = optimise(proj, budget, set(sol.squad.platform_id), max_trades=0, lock_squad=True, balance=balance)
            plan = simulate(sol.squad, n_sims=1500)
        hold = optimise(proj, budget, roster_ids, max_trades=0, lock_squad=True)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Expected pts", sol.expected_md_pts, delta=round(sol.expected_md_pts - hold.expected_md_pts, 1), help="Plain expectation of the chosen squad, whatever the risk mode")
        m2.metric("Cost", f"{sol.cost}/{budget}")
        m3.metric("In-round gain (sim)", plan.gain)
        m4.metric("Risk", f"{mode_r} · ±{float(sol.squad.md_sd.pow(2).sum() ** 0.5):.1f}", help="Standard deviation of the squad's matchday total (independent players)")
        if lam:
            st.caption(f"Status {sol.status} · optimised on expected − {lam:+.2f} × uncertainty, then re-scored on the plain expectation.")
        pl = lambda names: [{"name": n, "pos": proj.loc[proj.name == n, "pos"].iloc[0], "price": float(proj.loc[proj.name == n, "quotation"].iloc[0])} for n in names if (proj.name == n).any()]
        TH.md(TH.trades(pl(sol.trades_out), pl(sol.trades_in), f"Cost {sol.cost} / {budget} · Captain {sol.captain.upper()} · Coach {sol.coach.upper()} · {sol.status}"))
        st.write("")
        TH.md(TH.lineup_board(sol.squad.to_dict("records"), "What-if squad"))
        if plan.notes:
            TH.md(TH.notes("In-round plan", [("AFTER T1", n) for n in plan.notes]))
        with st.expander("Table view"):
            show(_squad_table(sol.squad))


# ------------------------------------------------------------------------------------------ league-wide pages
def page_projections(proj: pd.DataFrame, md: int, mode: str):
    st.subheader(f"Projections — matchday {md}")
    if proj.empty:
        st.warning("No projection yet.")
        return
    f1, f2, f3, f4 = st.columns(4)
    pos = f1.multiselect("Position", ["Guard", "Forward", "Center", "Head Coach"], default=["Guard", "Forward", "Center"])
    teams = f2.multiselect("Team", sorted(proj.team.dropna().unique()))
    pmax = f3.slider("Max price", 4.0, float(proj.quotation.max()), float(proj.quotation.max()), 0.1)
    only_playing = f4.checkbox("Only players with a game", value=True)
    g1, g2, g3 = st.columns([2, 1, 1])
    q = g1.text_input("Search name")
    hide_inj = g2.checkbox("Hide injured / doubtful", value=False)
    view = g3.selectbox("Columns", ["Decision", "Usage & role", "Price", "All"])
    df = proj[proj.pos.isin(pos) & (proj.quotation <= pmax)]
    if teams:
        df = df[df.team.isin(teams)]
    if only_playing:
        df = df[df.games_md > 0]
    if hide_inj:
        df = df[df.prob_play >= 1]
    if q:
        df = df[df.name.str.contains(q, case=False)]
    base = ["name", "pos", "team", "quotation", "nights", "prob_play"]
    decision = ["min_hat", "rate_hat", "md_pts", "floor", "md_p90", "value", "horizon_pts", "popularity"]
    usage_cols = ["starter_last", "shot_share", "fga_per_min", "usage_delta", "min_delta", "role_signal", "fd_pg", "blka_pg"]
    price_cols = ["price_base", "price_delta", "value", "horizon_pts", "popularity"]
    cols = base + {"Decision": decision, "Usage & role": usage_cols, "Price": price_cols,
                   "All": decision + usage_cols + ["price_base", "price_delta"]}[view]
    if "elite_own" in df and view in ("Decision", "All"):
        cols.append("elite_own")
    if mode == "team":
        cols.append("in_roster")
    cols += ["risk", "flags"]
    cols = [c for c in dict.fromkeys(cols) if c in df]
    pop_pct = df.assign(popularity=(df.popularity.fillna(0) * 100).round(0))
    show(pop_pct[cols].sort_values("md_pts", ascending=False), height=600)
    st.caption("Scatter: price vs expected points (size = p90).")
    ch = alt.Chart(df[df.pos != "Head Coach"]).mark_circle().encode(
        x=alt.X("quotation", title="price"), y=alt.Y("md_pts", title="expected pts"),
        size=alt.Size("md_p90", legend=None), color="pos",
        tooltip=["name", "team", "quotation", "md_pts", "md_p90", "nights", "flags"],
    ).interactive().properties(height=380)
    st.altair_chart(ch, width="stretch")


def dvp_targets(proj: pd.DataFrame) -> pd.DataFrame:
    """One row per (team, opponent, night, position) this matchday with the opponent's DvP and the best options."""
    dvp = csv("dvp.csv")
    if dvp.empty or proj.empty:
        return pd.DataFrame(columns=["night", "team", "opponent", "home", "position", "DvP", "rank", "games", "win %", "best options"])
    dvp_idx = dvp.set_index(["team", "fpos"])
    rows, seen = [], set()
    for r in proj[proj.pos != "Head Coach"].itertuples():
        for g in r.games:
            key = (r.team_off, g["opp"], g["turn"], r.pos)
            if key in seen:
                continue
            seen.add(key)
            try:
                d = dvp_idx.loc[(g["opp"], r.pos)]
            except KeyError:
                continue
            cands = proj[(proj.team_off == r.team_off) & (proj.pos == r.pos)].nlargest(3, "md_pts")
            rows.append({"night": f"T{g['turn']}", "team": r.team, "opponent": g["opp"], "home": "home" if g["home"] else "away",
                         "position": r.pos, "DvP": round(float(d.piroe_shrunk), 1), "rank": int(d.rank_weak_to_strong), "games": int(d.games),
                         "win %": round(100 * g["pw"]), "best options": ", ".join(f"{c.name} ({c.quotation}, {c.md_pts:.0f})" for c in cands.itertuples())})
    return pd.DataFrame(rows).sort_values("DvP", ascending=False) if rows else pd.DataFrame(columns=["night", "team", "opponent", "home", "position", "DvP", "rank", "games", "win %", "best options"])


def page_dvp(proj: pd.DataFrame, md: int):
    dvp = csv("dvp.csv")
    if dvp.empty:
        st.warning("No DvP yet.")
        return
    st.subheader(f"Who to target in matchday {md}")
    st.caption("Each row is a game this matchday where the opponent leaks PIR to a position. Pick players of that position from the listed team. "
               "DvP = PIR over expectation conceded per game (shrunk toward 0 with only a few games played); + means the defence is weak there.")
    if not proj.empty:
        tgt = dvp_targets(proj)
        good = tgt[tgt.DvP >= 1.0]
        bad = tgt[tgt.DvP <= -1.5].sort_values("DvP")
        st.markdown("**Target** (opponent leaks to this position):")
        st.dataframe(good.head(12), width="stretch", hide_index=True, column_config=DVP_COL)
        st.markdown("**Avoid** (opponent stifles this position):")
        st.dataframe(bad.head(8), width="stretch", hide_index=True, column_config=DVP_COL)
    st.divider()
    st.subheader("Full matrix — PIR over expectation conceded per game (this season)")
    st.caption("Red = the team leaks PIR to that position (target its opponents' players of that position); blue = it stifles it. Hover a cell for games played.")
    piv = dvp.pivot(index="team", columns="fpos", values="piroe_shrunk")[["Guard", "Forward", "Center"]]
    heat = dvp.copy()
    ch = alt.Chart(heat).mark_rect().encode(
        x=alt.X("fpos:N", title=None, sort=["Guard", "Forward", "Center"]),
        y=alt.Y("team:N", sort=alt.EncodingSortField("piroe_shrunk", op="mean", order="descending")),
        color=alt.Color("piroe_shrunk:Q", scale=alt.Scale(scheme="redblue", domainMid=0, reverse=True), title="PIRoE"),
        tooltip=["team", "fpos", alt.Tooltip("piroe_shrunk", format=".1f"), alt.Tooltip("pir_allowed", format=".1f"), "games"],
    ).properties(height=520)
    text = alt.Chart(heat).mark_text(fontSize=11).encode(
        x=alt.X("fpos:N", sort=["Guard", "Forward", "Center"]),
        y=alt.Y("team:N", sort=alt.EncodingSortField("piroe_shrunk", op="mean", order="descending")),
        text=alt.Text("piroe_shrunk:Q", format="+.1f"))
    st.altair_chart(ch + text, width="stretch")
    st.dataframe(piv.round(1), width="stretch")
    split = csv("dvp_split.csv")
    if not split.empty:
        st.subheader("Starters vs bench split (stronger shrinkage)")
        st.dataframe(split.pivot_table(index="team", columns=["fpos", "unit"], values="piroe_shrunk").round(1), width="stretch")


def page_player(proj: pd.DataFrame, mode: str):
    pg = player_games()
    pm = D.load_csv("player_map.csv", dtype={"platform_id": str, "person_code": str})
    if proj.empty or pg.empty:
        st.warning("No data yet.")
        return
    field = proj[proj.pos != "Head Coach"]
    names_all = sorted(field.name.tolist())
    if mode == "team" and field.in_roster.any():
        first = field[field.in_roster].sort_values("md_pts", ascending=False).name.iloc[0]
    else:
        first = field.sort_values("md_pts", ascending=False).name.iloc[0]
    name = st.selectbox("Player", names_all, index=names_all.index(first))
    row = proj[proj.name == name].iloc[0]
    code = pm.loc[pm.platform_id.astype(str) == row.platform_id, "person_code"]
    code = str(code.iloc[0]) if len(code) and isinstance(code.iloc[0], str) else None
    a, b, c, d, e = st.columns(5)
    a.metric("Price", row.quotation)
    b.metric("Expected (MD)", row.md_pts)
    c.metric("p90", row.md_p90)
    d.metric("Proj. minutes", row.min_hat)
    e.metric("PIR / min", row.rate_hat)
    st.write(row["why"])
    if isinstance(row["flags"], str) and row["flags"]:
        st.warning(row["flags"])
    hist = pg[pg.player_code.astype(str) == code].sort_values("date_utc") if code else pd.DataFrame()
    if len(hist):
        hist = hist.assign(game=lambda d: "R" + d["round"].astype(str) + " " + d.apply(lambda r: ("vs " if r.home else "@ ") + r.opponent, axis=1))
        base = alt.Chart(hist).encode(x=alt.X("game:N", sort=None, title=None))
        bars = base.mark_bar().encode(y=alt.Y("pir:Q", title="PIR"), color=alt.condition(alt.datum.starter, alt.value("#1f77b4"), alt.value("#aec7e8")),
                                      tooltip=["game", "minutes", "pir", "pts", "reb", "ast", "starter"])
        line = base.mark_line(color="#d62728", point=True).encode(y=alt.Y("minutes:Q", title="minutes"))
        st.altair_chart(alt.layer(bars, line).resolve_scale(y="independent").properties(height=320), width="stretch")
        st.dataframe(hist[["round", "game", "minutes", "starter", "pts", "reb", "ast", "stl", "blk", "tov", "pf", "fd", "pir"]].round(1), width="stretch", hide_index=True)
    else:
        st.info("No box-score rows matched this player this season.")
    st.caption("Game log: 2026-27 season only (earlier seasons are not used anywhere in the model).")
    st.subheader("Upcoming games in this matchday")
    st.table(pd.DataFrame(row.games))
    pr = prices()
    if len(pr):
        ph = pr[pr.player_id == row.platform_id][["matchday", "quotation", "avg_pts", "popularity"]]
        st.subheader("Price log")
        st.dataframe(ph, hide_index=True)


def page_top100():
    own = csv("top_ownership.csv")
    rost = D.load_csv("top_rosters.csv", dtype={"player_id": str})
    ins = D.PROCESSED / "top_insights.md"
    if own.empty or rost.empty:
        st.warning("Top-100 crawl not run yet.")
        return
    st.subheader("Elite ownership vs the crowd")
    st.caption("Above the diagonal = the top-100 managers own the player more than the crowd does — that is where their edge is.")
    if "global_pct" in own:
        ch = alt.Chart(own[own.teams >= 5]).mark_circle(size=80).encode(
            x=alt.X("global_pct", title="global ownership %"), y=alt.Y("own_pct", title="top-100 ownership %"),
            color="pos", tooltip=["player", "club", "price", "own_pct", "global_pct", "captain"]).interactive().properties(height=380)
        st.altair_chart(ch, width="stretch")
    st.dataframe(own.head(40), width="stretch", hide_index=True, column_config={
        "player": COL["player"], "pos": COL["pos"], "club": COL["club"], "price": COL["price"],
        "teams": st.column_config.NumberColumn("Teams", help="Number of top-100 teams owning the player"),
        "field": st.column_config.NumberColumn("On field", help="Of those, how many had him in the starting six (not bench)"),
        "captain": st.column_config.NumberColumn("Captain", help="How many top-100 teams captained him"),
        "own_pct": st.column_config.NumberColumn("Top-100 %", format="%.0f%%"),
        "global_pct": st.column_config.NumberColumn("Global %", help="Share of all managers owning him", format="%.0f%%"),
        "edge": st.column_config.NumberColumn("Edge pp", help="Top-100 % minus global % — positive = the elite see something the crowd misses", format="%+.0f"),
    })
    st.subheader("Ownership over time (top 100)")
    trend = rost.groupby(["matchday", "player"]).team_id.nunique().reset_index(name="teams")
    top_players = trend.groupby("player").teams.max().nlargest(12).index
    st.altair_chart(alt.Chart(trend[trend.player.isin(top_players)]).mark_line(point=True).encode(
        x="matchday:O", y="teams:Q", color="player:N", tooltip=["player", "matchday", "teams"]).properties(height=360), width="stretch")
    if ins.exists():
        with st.expander("Full insights"):
            st.markdown(ins.read_text(encoding="utf-8"))


def page_market(proj: pd.DataFrame):
    pr = prices()
    if pr.empty:
        st.warning("No price log yet.")
        return
    st.subheader("Price changes between pulls")
    last_two = sorted(pr.matchday.unique())[-2:]
    if len(last_two) == 2:
        a = pr[pr.matchday == last_two[0]].set_index("player_id")
        b = pr[pr.matchday == last_two[1]].set_index("player_id")
        j = b[["first_name", "last_name", "position", "team", "quotation", "avg_pts", "popularity"]].join(a[["quotation"]].rename(columns={"quotation": "prev"}), how="left")
        j["change"] = (j.quotation - j.prev).round(1)
        st.dataframe(j.sort_values("change", ascending=False), width="stretch", column_config={
            "quotation": COL["quotation"], "prev": st.column_config.NumberColumn("Prev price", format="%.1f"),
            "avg_pts": st.column_config.NumberColumn("Avg pts", help="Platform average fantasy points per matchday", format="%.1f"),
            "popularity": st.column_config.NumberColumn("Global own", help="Share of all managers owning the player (0–1)", format="%.2f"),
            "change": st.column_config.NumberColumn("Δ price", help="Change since the previous matchday snapshot", format="%+.1f"),
        })
    else:
        st.info("Only one price snapshot so far — changes appear from the second matchday pull.")
    st.subheader("Ownership vs expected points")
    st.caption("Bottom-right = popular but projected low (fade); top-left = unpopular but projected high (differential).")
    if not proj.empty:
        ch = alt.Chart(proj[proj.pos != "Head Coach"]).mark_circle().encode(
            x=alt.X("popularity", title="ownership"), y=alt.Y("md_pts", title="expected pts"), color="pos",
            tooltip=["name", "team", "quotation", "md_pts", "popularity"]).interactive().properties(height=380)
        st.altair_chart(ch, width="stretch")


def page_model_health(mode: str):
    st.subheader("Backtest (walk-forward, per round)")
    st.caption("Mean absolute error of the projection vs two naive baselines; lower is better. The model is re-fitted on the rounds before each tested round.")
    bt = csv("backtest_rounds.csv")
    if not bt.empty:
        summ = []
        for r, g in bt.groupby("round"):
            summ.append({"round": r, "n": len(g), "MAE model": (g.model - g.actual_pir).abs().mean(),
                         "MAE season-mean": (g.base_mean - g.actual_pir).abs().mean(), "MAE last-3": (g.base_last3 - g.actual_pir).abs().mean()})
        s = pd.DataFrame(summ).round(2)
        st.dataframe(s, hide_index=True)
        long = s.melt(id_vars=["round", "n"], var_name="estimator", value_name="MAE")
        st.altair_chart(alt.Chart(long).mark_line(point=True).encode(x="round:O", y="MAE:Q", color="estimator:N").properties(height=300), width="stretch")
    ev = D.PROCESSED / "evaluation.md"
    if ev.exists():
        with st.expander("Projection vs actual platform points (per round)"):
            st.markdown(ev.read_text(encoding="utf-8"))
    rec = csv("reconcile.csv")
    if not rec.empty:
        st.subheader("Scoring reconciliation (platform vs official)")
        st.write(rec.status.value_counts().to_frame("count").T)
    fe = D.load_csv("../external/fantasyedge_players.csv", dtype={"player_id": str}) if (D.DATA / "external" / "fantasyedge_players.csv").exists() else pd.DataFrame()
    _md, proj = proj_data()
    if len(fe) and "proj_pir_est" in fe and not proj.empty:
        st.subheader("Cross-source check — Fantasy Edge IQ projection vs ours")
        st.caption("Divergence detector, not a benchmark: their model blends 40% this season / 60% 2025-26, ours is this season only. "
                   "Large gaps are worth a look at the player's game log; agreement means little.")
        m = proj[(proj.pos != "Head Coach") & (proj.games_md > 0)].merge(fe[["player_id", "proj_pir_est", "popularity_pct"]], left_on="platform_id", right_on="player_id", how="inner")
        m["theirs"] = pd.to_numeric(m.proj_pir_est, errors="coerce")
        m = m.dropna(subset=["theirs"])
        if len(m):
            m["gap"] = (m.md_pts - m.theirs).round(1)
            k1, k2, k3 = st.columns(3)
            k1.metric("Players matched", len(m))
            k2.metric("Correlation", f"{m[['md_pts', 'theirs']].corr().iloc[0, 1]:.2f}")
            k3.metric("Mean abs gap", f"{m.gap.abs().mean():.1f}")
            st.dataframe(m.sort_values("gap", key=lambda s_: s_.abs(), ascending=False).head(15)[["name", "pos", "team", "quotation", "md_pts", "theirs", "gap", "min_hat", "risk"]],
                         width="stretch", hide_index=True, column_config={**{c: COL[c] for c in ("name", "pos", "team", "quotation", "md_pts", "min_hat", "risk")},
                         "theirs": st.column_config.NumberColumn("Theirs (proj PIR)", format="%.1f"), "gap": st.column_config.NumberColumn("Ours − theirs", format="%+.1f")})
            st.caption(f"Their file pulled {fe.pulled_at.iloc[0] if 'pulled_at' in fe else '—'}.")
    if mode == "team":
        st.subheader("Last pipeline log")
        st.code(re.sub(r"\x1b\[[0-9;]*m", "", D.pipeline_status()["log"])[-6000:])


# ------------------------------------------------------------------------------------------ overview
def traps(proj: pd.DataFrame, n: int = 8) -> pd.DataFrame:
    """Popular but projected low: ownership percentile minus expected-points percentile among players with a game."""
    f = proj[(proj.pos != "Head Coach") & (proj.games_md > 0)].copy()
    if f.empty:
        return f
    f["popularity"] = (f.popularity.fillna(0) * 100).round(0)
    f["trap"] = ((f.popularity.rank(pct=True) - f.md_pts.rank(pct=True)) * 100).round(0)
    f = f[(f.popularity >= 10) & (f.trap > 0)].sort_values("trap", ascending=False).head(n)
    return f[["name", "pos", "team", "quotation", "popularity", "md_pts", "floor", "value", "trap", "risk"]]


def sell_candidates(proj: pd.DataFrame, n: int = 6) -> pd.DataFrame:
    """Own squad ranked for selling: low 3-week value per credit, price already appreciated, hard next-5."""
    field = proj[(proj.pos != "Head Coach") & (proj.games_md > 0)].copy()
    if field.empty or not field.in_roster.any():
        return pd.DataFrame()
    fdr = csv("fdr.csv")
    nxt = fdr.groupby("team").next_n_avg.first() if len(fdr) else pd.Series(dtype=float)
    field["next_n_avg"] = field.team_off.map(nxt)
    field["h_value"] = field.horizon_pts / field.quotation.clip(lower=1)
    # percentiles against the whole league (not within the squad), so a star is never a "sell" just for being expensive
    pd_ = field.price_delta.fillna(0) if "price_delta" in field else pd.Series(0.0, index=field.index)
    score = (field.h_value.rank(pct=True, ascending=False) * 0.5
             + pd_.rank(pct=True) * 0.25
             + field.next_n_avg.fillna(field.next_n_avg.mean() if field.next_n_avg.notna().any() else 3).rank(pct=True) * 0.25)
    field["sell"] = (score * 100).round(0)
    sq = field[field.in_roster].copy()
    sq["why_sell"] = sq.apply(lambda r: " · ".join(x for x in (
        f"{r.h_value:.1f} 3-wk pts/credit" if pd.notna(r.h_value) else "",
        f"+{r.price_delta:.1f} since start" if pd.notna(r.get("price_delta")) and r.price_delta > 0 else "",
        f"next-5 FDR {r.next_n_avg:.1f}" if pd.notna(r.next_n_avg) and r.next_n_avg >= 3 else "",
        r.risk if r.risk else "") if x), axis=1)
    return sq.sort_values("sell", ascending=False).head(n)[["name", "pos", "team", "quotation", "price_delta", "md_pts", "horizon_pts", "next_n_avg", "sell", "why_sell"]]


def page_overview(proj: pd.DataFrame, md: int, mode: str):
    st.subheader(f"Overview — matchday {md}")
    st.caption("Leaderboards from this season's box scores and the current projection; minimum samples in each title.")
    pg = player_games()
    u = csv("usage.csv")
    ctx = csv("team_context.csv")
    fdr = csv("fdr.csv")
    field = proj[(proj.pos != "Head Coach")].copy() if not proj.empty else pd.DataFrame()

    def board(title: str, df: pd.DataFrame, cols: list[str], cfg: dict | None = None):
        st.markdown(f"**{title}**")
        st.dataframe(df[cols].head(8), width="stretch", hide_index=True, height=320,
                     column_config={**{c: COL[c] for c in cols if c in COL}, **(cfg or {})})

    c1, c2 = st.columns(2)
    if len(pg):
        played = pg[pg.played]
        gmax = played.groupby("team").game_code.nunique().max()
        per = played.groupby(["player_code", "player_name", "team"]).agg(games=("game_code", "nunique"), min_pg=("minutes", "mean"), pir_pg=("pir", "mean")).reset_index()
        per = per.rename(columns={"player_name": "player"})
        with c1:
            board(f"Average PIR (min {gmax // 2 + 1} games)", per[per.games > gmax // 2].sort_values("pir_pg", ascending=False), ["player", "team", "games", "pir_pg", "min_pg"],
                  {"pir_pg": st.column_config.NumberColumn("PIR/G", format="%.1f"), "min_pg": st.column_config.NumberColumn("Min/G", format="%.1f")})
        with c2:
            per["pir_per_min"] = per.pir_pg / per.min_pg.clip(lower=1)
            board("PIR per minute (min 10 min/G)", per[(per.min_pg >= 10) & (per.games >= 3)].sort_values("pir_per_min", ascending=False), ["player", "team", "games", "pir_per_min", "min_pg"],
                  {"pir_per_min": st.column_config.NumberColumn("PIR/min", format="%.2f"), "min_pg": st.column_config.NumberColumn("Min/G", format="%.1f")})
    c3, c4 = st.columns(2)
    if len(field):
        with c3:
            board("Best value this matchday (exp pts per credit, with a game)", field[field.games_md > 0].sort_values("value", ascending=False), ["name", "pos", "team", "quotation", "md_pts", "value"])
        with c4:
            board("Most expected points this matchday", field[field.games_md > 0].sort_values("md_pts", ascending=False), ["name", "pos", "team", "quotation", "md_pts", "floor", "md_p90"])
    c5, c6 = st.columns(2)
    if len(u):
        with c5:
            board("Most minutes per game", u.sort_values("min_pg", ascending=False).rename(columns={"player_name": "player"}), ["player", "team", "games", "min_pg", "starts"],
                  {"min_pg": st.column_config.NumberColumn("Min/G", format="%.1f"), "starts": st.column_config.NumberColumn("Starts")})
        with c6:
            board("Highest shot usage (min 10 min/G)", u[(u.min_pg >= 10) & (u.games >= 3)].sort_values("shot_share", ascending=False).rename(columns={"player_name": "player"}),
                  ["player", "team", "shot_share", "fga_per_min", "role_signal"])
    c7, c8 = st.columns(2)
    if len(fdr):
        with c7:
            nxt = fdr.groupby("team").agg(next_n_avg=("next_n_avg", "first"), opponents=("opponent", lambda s: ", ".join(s))).reset_index().sort_values("next_n_avg")
            board("Easiest next-5 runs (FDR, 1 easy – 5 hard)", nxt, ["team", "next_n_avg", "opponents"],
                  {"opponents": st.column_config.TextColumn("Next five", width="large")})
    if len(ctx):
        with c8:
            board("Fastest environments (possessions per game)", ctx.sort_values("pace", ascending=False), ["team", "pace", "pir_allowed", "fdr"],
                  {"pir_allowed": st.column_config.NumberColumn("PIR allowed", format="%.1f")})
    if len(field):
        st.markdown("**Traps — popular but projected low**")
        st.caption("Trap score = global-ownership percentile minus expected-points percentile among players with a game; the crowd owns them, the model doesn't.")
        show(traps(field))
    if len(u) and (u.role_signal.fillna("") != "").any():
        st.markdown("**Role changes (last 3 games vs season)**")
        rc = u[u.role_signal.fillna("") != ""].rename(columns={"player_name": "player"})
        st.dataframe(rc[["player", "team", "role_signal", "min_pg", "min_delta_last3", "fga_per_min", "usage_delta_last3", "shot_share"]], width="stretch", hide_index=True, column_config={
            "role_signal": COL["role_signal"], "shot_share": COL["shot_share"], "fga_per_min": COL["fga_per_min"],
            "min_pg": st.column_config.NumberColumn("Min/G", format="%.1f"), "min_delta_last3": COL["min_delta"], "usage_delta_last3": COL["usage_delta"]})


def page_team_context():
    ctx = csv("team_context.csv")
    if ctx.empty:
        st.warning("No team context yet — run `elfa build`.")
        return
    st.subheader("Team context — this season only")
    st.caption("Per-game environment for and against each club. Scores are percentiles among the 20 clubs (100 = most). "
               "FDR = 5 − 4 × ease/100, where ease = 40% PIR allowed + 20% points allowed + 20% pace + 10% FGA allowed + 10% rebounds allowed.")
    view = st.radio("View", ["Matchup", "Allowed (defence)", "For (offence)"], horizontal=True)
    if view == "Matchup":
        cols = ["team", "games", "pace", "pir_allowed", "pts_allowed", "fga_allowed", "reb_allowed", "defence_weakness_score", "matchup_ease", "fdr"]
    elif view == "Allowed (defence)":
        cols = ["team", "games", "pts_allowed", "pir_allowed", "poss_allowed", "fga_allowed", "fg2a_allowed", "fg3a_allowed", "fta_allowed", "oreb_allowed", "dreb_allowed", "ast_allowed", "stl_allowed", "tov_allowed", "blk_allowed", "efg_allowed", "ts_allowed"]
    else:
        cols = ["team", "games", "pts", "pir", "poss", "fga", "fg2a", "fg3a", "fta", "oreb", "dreb", "ast", "stl", "tov", "blk", "efg", "ts"]
    cfg = {c: COL[c] for c in cols if c in COL}
    for c in cols:
        if c not in cfg and c not in ("team", "games"):
            label = c.replace("_allowed", " allowed").replace("_", " ").upper() if not c.startswith(("efg", "ts")) else c.replace("_allowed", " allowed").replace("efg", "eFG%").replace("ts", "TS%")
            cfg[c] = st.column_config.NumberColumn(label, format="%.1f" if not c.startswith(("efg", "ts")) else "%.3f")
    st.dataframe(ctx[cols].sort_values("fdr" if "fdr" in cols else cols[2]), width="stretch", hide_index=True, column_config=cfg, height=760)
    st.caption("PIR allowed vs pace: top-right clubs are the fantasy-friendly matchups (fast and leaky).")
    ch = alt.Chart(ctx).mark_circle(size=120).encode(
        x=alt.X("pace", title="pace (possessions/game)"), y=alt.Y("pir_allowed", title="PIR allowed per game"),
        color=alt.Color("fdr", scale=alt.Scale(scheme="redyellowgreen", reverse=True), title="FDR"),
        tooltip=["team", "pace", "pir_allowed", "pts_allowed", "fdr"]).properties(height=380)
    text = alt.Chart(ctx).mark_text(dy=-12, fontSize=11).encode(x="pace", y="pir_allowed", text="team")
    st.altair_chart(ch + text, width="stretch")


# ------------------------------------------------------------------------------------------ captain
def _elite_captains() -> tuple[pd.Series, pd.Series]:
    """(captain count in the last played matchday, number of matchdays captained) per player name, from the top-100 crawl."""
    rost = csv("top_rosters.csv")
    if rost.empty or "captain" not in rost:
        return pd.Series(dtype=int), pd.Series(dtype=int)
    cap = rost[rost.captain.astype(str).str.lower().isin(["true", "1"])]
    last = cap[cap.matchday == rost.matchday.max()].groupby("player").team_id.nunique()
    mds = cap.groupby("player").matchday.nunique()
    return last, mds


def page_captain(proj: pd.DataFrame, md: int, mode: str):
    st.subheader(f"Captain — matchday {md}")
    if proj.empty:
        st.warning("No projection yet.")
        return
    field = proj[(proj.pos != "Head Coach") & (proj.games_md > 0)].copy()
    if field.empty:
        st.info("Nobody has a game in this matchday yet.")
        return
    field["floor"] = (field.md_pts - 1.2816 * field.md_sd).round(1)
    field["games_txt"] = field.games.map(lambda gs: " · ".join(f"T{g['turn']} {'vs' if g['home'] else '@'} {g['opp']} {g['fp']:.0f} ({g['pw']:.0%})" for g in gs))
    last, mds = _elite_captains()
    field["elite_cap"] = field.name.map(last).fillna(0).astype(int)
    field["elite_cap_mds"] = field.name.map(mds).fillna(0).astype(int)
    field["popularity"] = (field.popularity.fillna(0) * 100).round(0)
    if mode == "team":
        _tmd, roster = roster_state()
        cap_ids = {str(p["id"]) for p in roster.get("players", []) if p.get("is_captain")}
        field["captain_now"] = field.platform_id.astype(str).isin(cap_ids)

    f1, f2, f3 = st.columns(3)
    rank_by = f1.selectbox("Rank by", ["Expected pts (ceiling play)", "Floor p10 (safe play)", "p90 (max ceiling)"],
                           help="Doubling the captain adds exactly his matchday points: the expected gain is his expected points, the risk is his spread.")
    min_games = f2.selectbox("Games this matchday", ["any", "2+"]) if field.games_md.max() > 1 else "any"
    only_mine = f3.checkbox("Only my squad", value=False) if mode == "team" else False
    df = field
    if min_games.startswith("2"):
        df = df[df.games_md >= 2]
    if only_mine:
        df = df[df.in_roster]
    key = {"Expected pts (ceiling play)": "md_pts", "Floor p10 (safe play)": "floor", "p90 (max ceiling)": "md_p90"}[rank_by]
    cols = ["name", "pos", "team", "quotation", "nights", "md_pts", "md_sd", "floor", "md_p90", "games_txt", "elite_cap", "elite_cap_mds", "popularity"]
    if mode == "team":
        cols += ["in_roster", "captain_now"]
    cols.append("flags")
    show(df.sort_values(key, ascending=False)[cols].head(40), height=520)

    st.caption("Expected points vs uncertainty. Top-left = high and steady (safe captain); top-right = high but volatile (ceiling captain). Size = p90.")
    ch = alt.Chart(df.nlargest(60, "md_pts")).mark_circle().encode(
        x=alt.X("md_sd", title="uncertainty (±)"), y=alt.Y("md_pts", title="expected pts"),
        size=alt.Size("md_p90", legend=None), color="pos",
        tooltip=["name", "team", "quotation", "md_pts", "md_sd", "floor", "md_p90", "nights", "elite_cap"],
    ).interactive().properties(height=360)
    st.altair_chart(ch, width="stretch")

    tabs = st.tabs(["Night by night", "Elite choices"])
    with tabs[0]:
        st.caption("Best single-game options per night. Use this to move the armband after night 1: it may only go to a starter who has NOT yet played.")
        rows = [{"night": f"T{g['turn']}", "name": r.name, "pos": r.pos, "team": r.team, "opp": ("vs " if g["home"] else "@ ") + g["opp"],
                 "exp": g["fp"], "win %": round(100 * g["pw"]), "quotation": r.quotation}
                for r in df.itertuples() for g in r.games]
        nb = pd.DataFrame(rows)
        if len(nb):
            nb = nb.sort_values(["night", "exp"], ascending=[True, False]).groupby("night").head(8)
            st.dataframe(nb, width="stretch", hide_index=True, column_config={
                "night": COL["night"], "name": COL["name"], "pos": COL["pos"], "team": COL["team"], "quotation": COL["quotation"],
                "exp": st.column_config.NumberColumn("Exp pts (game)", format="%.1f"), "win %": DVP_COL["win %"]})
    with tabs[1]:
        rost = csv("top_rosters.csv")
        if rost.empty:
            st.info("Top-100 crawl not run yet.")
        else:
            cap = rost[rost.captain.astype(str).str.lower().isin(["true", "1"])]
            byd = cap.groupby(["matchday", "player"]).team_id.nunique().reset_index(name="teams")
            top = byd.sort_values(["matchday", "teams"], ascending=[True, False]).groupby("matchday").head(3)
            st.caption("Who the top-100 managers captained, per matchday (teams). The crowd's default is Vezenkov; the elite move the armband to the matchup.")
            st.altair_chart(alt.Chart(top).mark_bar().encode(
                x="matchday:O", y="teams:Q", color="player:N", tooltip=["matchday", "player", "teams"]).properties(height=300), width="stretch")
            st.dataframe(top.pivot(index="matchday", columns="player", values="teams").fillna(0).astype(int), width="stretch")
    TH.md(TH.notes("Captain rules", [
        ("×2", "The captain scores double. He must be one of the five starters (not the sixth man or bench)."),
        ("NIGHTS", "On multi-night matchdays the captain's games are summed; after a night the armband can move only to a starter who has not played yet."),
        ("AVERAGE", "A postponed game credited with the player's average does not double."),
        ("MODEL", "Expected gain of captaining = expected points; floor = 10th percentile of the projection; p90 = ceiling."),
    ]))


# ------------------------------------------------------------------------------------------ fixtures & schedule
def page_fixtures(proj: pd.DataFrame, md: int):
    sched = schedule_df()
    if sched.empty:
        st.warning("No schedule yet.")
        return
    rounds, nights = current_rounds_and_nights(sched)
    night_of = {d: i + 1 for i, d in enumerate(nights)}
    cur = sched[sched["round"].isin(rounds)].copy()
    cur["night"] = cur.date_utc.dt.strftime("%Y-%m-%d").map(night_of).map(lambda t: f"T{int(t)}" if pd.notna(t) else "")
    cur["local"] = cur.date_utc.map(_local)
    od = _latest_odds()
    if len(od):
        cur = cur.merge(od[["home", "away", "home_win_prob", "home_spread", "total"]], on=["home", "away"], how="left")
        cur["home_win"] = (cur.home_win_prob * 100).round(0)
        cur = cur.rename(columns={"home_spread": "spread"})
    fdr = csv("fdr.csv")
    fdr_of = {(r.team, r.game_code): r.fdr for r in fdr.itertuples()} if len(fdr) else {}
    if fdr_of:
        cur["fdr_home"] = [fdr_of.get((r.home, r.game_code)) for r in cur.itertuples()]
        cur["fdr_away"] = [fdr_of.get((r.away, r.game_code)) for r in cur.itertuples()]
    st.subheader(f"Matchday {md} — {' + '.join(f'round {r}' for r in rounds)} · {len(nights)} game night(s)")
    st.caption("Tip-off times in Athens. Field↔bench swaps and captain changes are allowed between nights, for players who have not played yet. "
               "FDR = how hard the fixture is for that side's players to score fantasy points (1 easy – 5 hard).")
    cols = ["night", "local", "home", "away"] + (["home_win", "spread", "total"] if len(od) else []) + (["fdr_home", "fdr_away"] if fdr_of else []) + ["venue"]
    st.dataframe(cur[cols], width="stretch", hide_index=True, height=min(60 + 36 * len(cur), 560), column_config={
        **{c: COL[c] for c in cols if c in COL},
        "fdr_home": st.column_config.NumberColumn("FDR home side", help="Fixture difficulty for the home team's players (1 easy – 5 hard)", format="%.1f"),
        "fdr_away": st.column_config.NumberColumn("FDR away side", help="Fixture difficulty for the away team's players (1 easy – 5 hard)", format="%.1f")})

    # team × night grid
    teams = sorted(set(sched.home) | set(sched.away))
    grid = pd.DataFrame(index=teams, columns=[f"T{i + 1}" for i in range(len(nights))]).fillna("")
    for r in cur.itertuples():
        if r.night:
            grid.loc[r.home, r.night] = f"vs {r.away}"
            grid.loc[r.away, r.night] = f"@ {r.home}"
    grid["games_md_team"] = (grid != "").sum(axis=1)
    st.markdown("**Who plays when** — balance your squad across nights so you can react after T1:")
    st.dataframe(grid.sort_values("games_md_team", ascending=False), width="stretch", column_config={"games_md_team": COL["games_md_team"]})

    st.divider()
    n_rounds = st.slider("Horizon (rounds ahead)", 2, 10, 5, help="One fantasy matchday = one EuroLeague round. The optimiser looks three matchdays ahead.")
    start = min(rounds) if rounds else int(sched[~sched.played]["round"].min())
    hor = sched[(sched["round"] >= start) & (sched["round"] < start + n_rounds) & (sched.phase == "RS")].copy()
    st.subheader(f"Horizon — rounds {start} to {start + n_rounds - 1}")
    st.caption("Each cell is the club's opponent in that round (vs = home, @ = away) and the fixture difficulty for the club's players (1 easy – 5 hard). "
               "Next-5 FDR = average over the next five games. Rest = days between the club's last played game and its first game of this matchday; min gap = shortest gap between consecutive games in the horizon.")
    cal = pd.DataFrame(index=teams, columns=[f"R{r}" for r in range(start, start + n_rounds)]).fillna("—")
    for g in hor.itertuples():
        fh, fa = fdr_of.get((g.home, g.game_code)), fdr_of.get((g.away, g.game_code))
        cal.loc[g.home, f"R{g.round}"] = f"vs {g.away}" + (f" · {fh:.1f}" if fh is not None else "")
        cal.loc[g.away, f"R{g.round}"] = f"@ {g.home}" + (f" · {fa:.1f}" if fa is not None else "")
    cal["games_h"] = (cal != "—").sum(axis=1)
    if len(fdr):
        cal["next_n_avg"] = fdr.groupby("team").next_n_avg.first()
    cal["home_h"] = cal.apply(lambda r: sum(str(v).startswith("vs") for v in r.values[:n_rounds]), axis=1)
    # rest and gaps
    long = pd.concat([sched[["date_utc", "played", "round"]].assign(team=sched.home), sched[["date_utc", "played", "round"]].assign(team=sched.away)])
    rest, gap = {}, {}
    for t, g in long.groupby("team"):
        g = g.sort_values("date_utc")
        last_played = g[g.played].date_utc.max()
        first_cur = g[g["round"].isin(rounds)].date_utc.min()
        rest[t] = (first_cur - last_played).days if pd.notna(last_played) and pd.notna(first_cur) else None
        h = g[(g["round"] >= start) & (g["round"] < start + n_rounds)].date_utc.sort_values()
        gap[t] = int(h.diff().dt.days.min()) if len(h) > 1 else None
    cal["rest"] = pd.Series(rest)
    cal["gap"] = pd.Series(gap)
    st.dataframe(cal.sort_values(["next_n_avg", "games_h"] if "next_n_avg" in cal else ["games_h", "home_h"], ascending=[True, False]), width="stretch",
                 column_config={k: COL[k] for k in ("games_h", "home_h", "rest", "gap", "next_n_avg") if k in cal})
    st.markdown("**Results so far** (for context — the model uses the box scores, not the scores):")
    done = sched[sched.played].copy()
    if len(done):
        done["score"] = done.home_score.astype(int).astype(str) + "–" + done.away_score.astype(int).astype(str)
        done["local"] = done.date_utc.map(_local)
        with st.expander(f"{len(done)} games played"):
            st.dataframe(done[["round", "local", "home", "score", "away"]].sort_values(["round", "local"], ascending=[False, True]), width="stretch", hide_index=True)


# ------------------------------------------------------------------------------------------ game script (odds)
def page_game_script(proj: pd.DataFrame, md: int):
    od = odds_df()
    st.subheader(f"Game script — bookmaker view of matchday {md}")
    if od.empty:
        st.warning("No odds pulled yet (ODDS_API_KEY not set, or no pull since the last deadline). The projection falls back to model margins.")
        return
    sched = schedule_df()
    _rounds, nights = current_rounds_and_nights(sched)
    night_of = {d: i + 1 for i, d in enumerate(nights)}
    latest = _latest_odds()
    latest = latest.merge(sched[["home", "away", "round", "date_utc"]], on=["home", "away"], how="left")
    latest["night"] = latest.date_utc.dt.strftime("%Y-%m-%d").map(night_of).map(lambda t: f"T{int(t)}" if pd.notna(t) else "")
    latest["local"] = latest.commence.map(_local)
    latest["home_win"] = (latest.home_win_prob * 100).round(0)
    latest["favourite"] = latest.apply(lambda r: (f"{r.home} {r.home_win_prob:.0%}" if r.home_win_prob >= 0.5 else f"{r.away} {1 - r.home_win_prob:.0%}") if pd.notna(r.home_win_prob) else "", axis=1)
    latest = latest.rename(columns={"home_spread": "spread"})
    abs_sp = latest.spread.abs()
    latest["blowout"] = pd.cut(abs_sp, [-1, 8, 12, 99], labels=["low", "medium", "HIGH"]).astype(str).replace("nan", "")
    med = latest.total.median()
    latest["scoring_env"] = pd.cut(latest.total - med, [-99, -4, 4, 99], labels=["slow", "average", "fast"]).astype(str).replace("nan", "")
    snaps = od.snapshot.nunique()
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Games priced", len(latest))
    k2.metric("Snapshots", snaps, help="Odds pulls on disk — the line-movement section compares the first and the latest")
    k3.metric("Latest pull", _local(od.snapshot.max()))
    k4.metric("Median total", f"{med:.1f}" if pd.notna(med) else "—")
    st.caption("How the projection uses this: −spread is the expected margin (drives the coach EV and minutes in lopsided games), the h2h probability is the 10% win bonus. "
               "The total is shown as a scoring-environment signal; it is not in the model yet (pace comes from the box scores).")
    cols = ["night", "local", "home", "away", "favourite", "home_win", "spread", "total", "blowout", "scoring_env", "books"]
    show(latest.sort_values(["date_utc", "spread"])[cols], height=min(60 + 36 * len(latest), 560))

    st.subheader("Who benefits")
    st.caption("Underdog starters in close games keep their minutes; heavy favourites rest starters late. Players listed = top expected points of each side this matchday.")
    if not proj.empty:
        rows = []
        for r in latest.itertuples():
            for side, code in (("home", r.home), ("away", r.away)):
                pl = proj[(proj.team_off == code) & (proj.pos != "Head Coach")].nlargest(3, "md_pts")
                wp = r.home_win_prob if side == "home" else 1 - r.home_win_prob
                rows.append({"night": r.night, "team": code, "role": "favourite" if wp >= 0.5 else "underdog", "win %": round(100 * wp) if pd.notna(wp) else None,
                             "spread": -r.spread if side == "home" else r.spread, "blowout": r.blowout,
                             "top players": ", ".join(f"{p.name} ({p.md_pts:.0f})" for p in pl.itertuples())})
        wb = pd.DataFrame(rows)
        st.dataframe(wb.sort_values(["night", "win %"], ascending=[True, False]), width="stretch", hide_index=True, column_config={
            "night": COL["night"], "team": COL["team"], "win %": DVP_COL["win %"], "blowout": COL["blowout"],
            "spread": st.column_config.NumberColumn("Margin", help="Expected margin for this team (positive = expected to win by)", format="%+.1f"),
            "top players": st.column_config.TextColumn("Top players (exp pts)", width="large")})

    if snaps > 1:
        st.subheader("Line movement")
        first = od[od.snapshot == od.snapshot.min()].set_index(["home", "away"])
        mv = latest.set_index(["home", "away"])
        mv["d_win"] = ((mv.home_win_prob - first.home_win_prob) * 100).round(1)
        mv["d_spread"] = (mv.spread - first.home_spread).round(1)
        mv["d_total"] = (mv.total - first.total).round(1)
        mv = mv.reset_index()
        st.caption(f"Change from the first snapshot ({_local(od.snapshot.min())}) to the latest. A moving line usually means injury or rotation news the market has priced in.")
        show(mv.sort_values("d_win", key=lambda s: s.abs(), ascending=False)[["night", "home", "away", "home_win", "d_win", "spread", "d_spread", "total", "d_total"]])
        hist = od.assign(game=od.home + " – " + od.away, home_win=od.home_win_prob * 100)
        st.altair_chart(alt.Chart(hist).mark_line(point=True).encode(
            x=alt.X("snapshot:T", title="pull (UTC)"), y=alt.Y("home_win:Q", title="home win %"), color=alt.Color("game:N", legend=alt.Legend(columns=2)),
            tooltip=["game", alt.Tooltip("snapshot:T", format="%d %b %H:%M"), alt.Tooltip("home_win:Q", format=".0f"), alt.Tooltip("home_spread:Q", format="+.1f"), alt.Tooltip("total:Q", format=".1f")],
        ).properties(height=340), width="stretch")
    else:
        st.info("One odds snapshot so far — line movement appears once the pipeline has pulled again (daily and 4 h / 1 h before the deadline).")


# ------------------------------------------------------------------------------------------ router
def render(mode: str):
    TH.inject_css()
    TH.altair_theme()
    md, proj = proj_data()
    header(mode, md)
    pages = (TEAM_PAGES + SCOUT_PAGES) if mode == "team" else SCOUT_PAGES
    page = st.sidebar.radio("Page", pages)
    if mode == "scout":
        st.sidebar.caption("Scouting app — league-wide data only. Updated by the pipeline before each matchday deadline.")

    if page == "Overview":
        page_overview(proj, md, mode)
    elif page == "Team context":
        page_team_context()
    elif page == "Recommendation":
        page_recommendation(proj, md)
    elif page == "What-if optimiser":
        page_whatif(proj)
    elif page == "Projections":
        page_projections(proj, md, mode)
    elif page == "Captain":
        page_captain(proj, md, mode)
    elif page == "Fixtures & schedule":
        page_fixtures(proj, md)
    elif page == "Game script (odds)":
        page_game_script(proj, md)
    elif page == "Defence vs position":
        page_dvp(proj, md)
    elif page == "Player":
        page_player(proj, mode)
    elif page == "Top 100 managers":
        page_top100()
    elif page == "Market & prices":
        page_market(proj)
    elif page == "Model health":
        page_model_health(mode)
