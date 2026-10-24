"""Shared page renderers for the two Streamlit apps.

mode = "team"  : the private app — all reports plus everything about my own squad.
mode = "scout" : the public scouting app — only league-wide reports (players, teams, market);
                 nothing about my team is loaded or shown.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

_ROOT = Path(__file__).resolve().parents[1]
for _p in (str(_ROOT), str(_ROOT / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from app import data as D

SLOT = {"starter": "Starter", "sixth": "6th man", "bench": "Bench (50%)", "coach": "Coach"}

TEAM_PAGES = ["Recommendation", "What-if optimiser"]
SCOUT_PAGES = ["Projections", "Defence vs position", "Player", "Top 100 managers", "Market & prices", "Model health"]

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


def header(mode: str, md: int):
    status = D.pipeline_status()
    if mode == "team":
        tmd, _roster = roster_state()
        st.title("🏀 EuroLeague Fantasy Agent")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Matchday", md or "—")
        c2.metric("Credits", tmd.get("credits", "—"))
        c3.metric("Trades left", f"{int(tmd.get('max_num_trades_per_matchday', 0)) - int(tmd.get('trades', 0))}" if tmd else "—")
        c4.metric("Total pts", tmd.get("total_pts", "—"))
        st.caption(f"{status['deadline']}  ·  {status['generated']}  ·  last run: {status['run_reason']}")
    else:
        st.title("🏀 EuroLeague Fantasy Scout")
        st.caption("League-wide projections, matchup analytics, elite-manager tendencies and market data for the EuroLeague Fantasy Challenge. "
                   "Scoring: PIR + 10% if the team wins; starters 100%, bench 50%, captain ×2.")
        c1, c2 = st.columns([1, 3])
        c1.metric("Matchday", md or "—")
        c2.caption(f"{status['deadline']}  ·  {scrub_team(status['generated'])}")


# ------------------------------------------------------------------------------------------ team pages
def _squad_table(sq: pd.DataFrame) -> pd.DataFrame:
    sq = sq.copy()
    sq["slot"] = sq.role.map(SLOT)
    sq["player"] = sq.apply(lambda r: f"{r['name']} (C)" if r.captain else r["name"], axis=1)
    cols = ["slot", "player", "pos", "team", "quotation", "nights", "md_pts", "md_p90", "why"]
    return sq[cols].rename(columns={"quotation": "price", "md_pts": "exp", "md_p90": "p90", "why": "justification"})


def page_recommendation():
    st.markdown(D.load_report("recommendation_latest.md"))


def page_whatif(proj: pd.DataFrame):
    tmd, roster = roster_state()
    roster_ids = {str(p["id"]) for p in roster.get("players", [])}
    st.subheader("Run the optimiser with your constraints")
    if proj.empty:
        st.warning("No projection yet.")
        return
    from elfa.model.inround import simulate
    from elfa.optimise.lineup import optimise

    names = sorted(proj.name.tolist())
    in_squad = sorted(proj[proj.in_roster].name.tolist())
    colA, colB = st.columns(2)
    keep = colA.multiselect("Must keep", in_squad)
    exclude = colB.multiselect("Exclude from consideration", names)
    colC, colD, colE = st.columns(3)
    trades = colC.slider("Max trades", 0, 4, int(tmd.get("max_num_trades_per_matchday", 4)) - int(tmd.get("trades", 0)) if tmd else 4)
    budget = colD.number_input("Budget", value=float(tmd.get("credits", 100.0)), step=0.1)
    balance = colE.checkbox("Night balance rule", value=True,
                            help="On multi-night matchdays keep ≥3 field players on night 1 and ≥2 bench players with later games, so you can react after the first night.")
    if st.button("Optimise", type="primary"):
        df = proj[~proj.name.isin(exclude)].copy()
        keep_ids = set(df[df.name.isin(keep)].platform_id)
        with st.spinner("solving…"):
            sol = optimise(df, budget, roster_ids, max_trades=trades, keep_ids=keep_ids, balance=balance)
            plan = simulate(sol.squad, n_sims=1500)
        hold = optimise(proj, budget, roster_ids, max_trades=0, lock_squad=True)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Expected pts", sol.expected_md_pts, delta=round(sol.expected_md_pts - hold.expected_md_pts, 1))
        m2.metric("Cost", f"{sol.cost}/{budget}")
        m3.metric("In-round gain (sim)", plan.gain)
        m4.metric("Status", sol.status)
        st.write(f"**OUT:** {', '.join(sol.trades_out) or '—'}  →  **IN:** {', '.join(sol.trades_in) or '—'}  ·  Captain **{sol.captain}**, coach **{sol.coach}**")
        show(_squad_table(sol.squad))
        for n in plan.notes:
            st.caption("• " + n)


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
    q = st.text_input("Search name")
    df = proj[proj.pos.isin(pos) & (proj.quotation <= pmax)]
    if teams:
        df = df[df.team.isin(teams)]
    if only_playing:
        df = df[df.games_md > 0]
    if q:
        df = df[df.name.str.contains(q, case=False)]
    cols = ["name", "pos", "team", "quotation", "nights", "prob_play", "min_hat", "rate_hat", "md_pts", "md_p90", "value", "horizon_pts", "popularity"]
    if "elite_own" in df:
        cols.append("elite_own")
    if mode == "team":
        cols.append("in_roster")
    cols.append("flags")
    pop_pct = df.assign(popularity=(df.popularity.fillna(0) * 100).round(0))
    show(pop_pct[cols].sort_values("md_pts", ascending=False), height=600)
    st.caption("Scatter: price vs expected points (size = p90).")
    ch = alt.Chart(df[df.pos != "Head Coach"]).mark_circle().encode(
        x=alt.X("quotation", title="price"), y=alt.Y("md_pts", title="expected pts"),
        size=alt.Size("md_p90", legend=None), color="pos",
        tooltip=["name", "team", "quotation", "md_pts", "md_p90", "nights", "flags"],
    ).interactive().properties(height=380)
    st.altair_chart(ch, width="stretch")


def page_dvp(proj: pd.DataFrame, md: int):
    dvp = csv("dvp.csv")
    if dvp.empty:
        st.warning("No DvP yet.")
        return
    st.subheader(f"Who to target in matchday {md}")
    st.caption("Each row is a game this matchday where the opponent leaks PIR to a position. Pick players of that position from the listed team. "
               "DvP = PIR over expectation conceded per game (shrunk toward 0 with only a few games played); + means the defence is weak there.")
    if not proj.empty:
        dvp_idx = dvp.set_index(["team", "fpos"])
        rows = []
        seen = set()
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
        tgt = pd.DataFrame(rows).sort_values("DvP", ascending=False)
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
    if mode == "team":
        st.subheader("Last pipeline log")
        st.code(re.sub(r"\x1b\[[0-9;]*m", "", D.pipeline_status()["log"])[-6000:])


# ------------------------------------------------------------------------------------------ router
def render(mode: str):
    md, proj = proj_data()
    header(mode, md)
    pages = (TEAM_PAGES + SCOUT_PAGES) if mode == "team" else SCOUT_PAGES
    page = st.sidebar.radio("Page", pages)
    if mode == "scout":
        st.sidebar.caption("Scouting app — league-wide data only. Updated by the pipeline before each matchday deadline.")

    if page == "Recommendation":
        page_recommendation()
    elif page == "What-if optimiser":
        page_whatif(proj)
    elif page == "Projections":
        page_projections(proj, md, mode)
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
