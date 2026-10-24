"""EuroLeague Fantasy Agent — dashboard (Streamlit).

Reads the files the GitHub Actions pipeline commits; the what-if page runs the real optimiser.
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

st.set_page_config(page_title="EuroLeague Fantasy Agent", page_icon="🏀", layout="wide")

SLOT = {"starter": "Starter", "sixth": "6th man", "bench": "Bench (50%)", "coach": "Coach"}


@st.cache_data(ttl=600)
def _proj():
    return D.load_projection()


@st.cache_data(ttl=600)
def _pg():
    return D.load_player_games()


@st.cache_data(ttl=600)
def _csv(name):
    return D.load_csv(name)


@st.cache_data(ttl=600)
def _prices():
    return D.load_prices()


@st.cache_data(ttl=600)
def _roster():
    return D.load_roster_state()


@st.cache_data(ttl=600)
def _sched():
    return D.load_schedule()


def _squad_table(sq: pd.DataFrame) -> pd.DataFrame:
    sq = sq.copy()
    sq["slot"] = sq.role.map(SLOT)
    sq["player"] = sq.apply(lambda r: f"{r['name']} (C)" if r.captain else r["name"], axis=1)
    cols = ["slot", "player", "pos", "team", "quotation", "nights", "md_pts", "md_p90", "why"]
    return sq[cols].rename(columns={"quotation": "price", "md_pts": "exp", "md_p90": "p90", "why": "justification"})


# ------------------------------------------------------------------------------------------
status = D.pipeline_status()
md, proj = _proj()
tmd, roster = _roster()
roster_ids = {str(p["id"]) for p in roster.get("players", [])}

st.title("🏀 EuroLeague Fantasy Agent")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Matchday", md or "—")
c2.metric("Credits", tmd.get("credits", "—"))
c3.metric("Trades left", f"{int(tmd.get('max_num_trades_per_matchday', 0)) - int(tmd.get('trades', 0))}" if tmd else "—")
c4.metric("Total pts", tmd.get("total_pts", "—"))
st.caption(f"{status['deadline']}  ·  {status['generated']}  ·  last run: {status['run_reason']}")

page = st.sidebar.radio(
    "Page",
    ["Recommendation", "What-if optimiser", "Projections", "Defence vs position", "Player", "Market & prices", "Model health"],
)

# ------------------------------------------------------------------------------------------
if page == "Recommendation":
    st.markdown(D.load_report("recommendation_latest.md"))

# ------------------------------------------------------------------------------------------
elif page == "What-if optimiser":
    st.subheader("Run the optimiser with your constraints")
    if proj.empty:
        st.warning("No projection yet.")
    else:
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
        balance = colE.checkbox("Night balance rule", value=True)
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
            st.dataframe(_squad_table(sol.squad), width="stretch", hide_index=True)
            for n in plan.notes:
                st.caption("• " + n)

# ------------------------------------------------------------------------------------------
elif page == "Projections":
    st.subheader(f"Projections — matchday {md}")
    if proj.empty:
        st.warning("No projection yet.")
    else:
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
        cols = ["name", "pos", "team", "quotation", "nights", "prob_play", "min_hat", "rate_hat", "md_pts", "md_p90", "value", "horizon_pts", "popularity", "in_roster", "flags"]
        st.dataframe(df[cols].sort_values("md_pts", ascending=False).rename(columns={"quotation": "price", "min_hat": "min", "rate_hat": "PIR/min", "md_pts": "exp", "md_p90": "p90"}),
                     width="stretch", hide_index=True, height=600)
        st.caption("Scatter: price vs expected points (size = p90).")
        ch = alt.Chart(df[df.pos != "Head Coach"]).mark_circle().encode(
            x=alt.X("quotation", title="price"), y=alt.Y("md_pts", title="expected pts"),
            size=alt.Size("md_p90", legend=None), color="pos",
            tooltip=["name", "team", "quotation", "md_pts", "md_p90", "nights", "flags"],
        ).interactive().properties(height=380)
        st.altair_chart(ch, width="stretch")

# ------------------------------------------------------------------------------------------
elif page == "Defence vs position":
    dvp = _csv("dvp.csv")
    if dvp.empty:
        st.warning("No DvP yet.")
    else:
        st.subheader("PIR over expectation conceded per game, this season (shrunk to league mean)")
        st.caption("Positive = the team leaks PIR to that position; negative = it stifles it. n = games.")
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
        split = _csv("dvp_split.csv")
        if not split.empty:
            st.subheader("Starters vs bench split (stronger shrinkage)")
            st.dataframe(split.pivot_table(index="team", columns=["fpos", "unit"], values="piroe_shrunk").round(1), width="stretch")

# ------------------------------------------------------------------------------------------
elif page == "Player":
    pg = _pg()
    pm = _csv("player_map.csv")
    if proj.empty or pg.empty:
        st.warning("No data yet.")
    else:
        names_all = sorted(proj[proj.pos != "Head Coach"].name.tolist())
        mine = proj[proj.in_roster & (proj.pos != "Head Coach")].sort_values("md_pts", ascending=False).name.tolist()
        default_ix = names_all.index(mine[0]) if mine else 0
        name = st.selectbox("Player", names_all, index=default_ix)
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
        prices = _prices()
        if len(prices):
            ph = prices[prices.player_id == row.platform_id][["matchday", "quotation", "avg_pts", "popularity"]]
            st.subheader("Price log")
            st.dataframe(ph, hide_index=True)

# ------------------------------------------------------------------------------------------
elif page == "Market & prices":
    prices = _prices()
    if prices.empty:
        st.warning("No price log yet.")
    else:
        st.subheader("Price changes between pulls")
        last_two = sorted(prices.matchday.unique())[-2:]
        if len(last_two) == 2:
            a = prices[prices.matchday == last_two[0]].set_index("player_id")
            b = prices[prices.matchday == last_two[1]].set_index("player_id")
            j = b[["first_name", "last_name", "position", "team", "quotation", "avg_pts", "popularity"]].join(a[["quotation"]].rename(columns={"quotation": "prev"}), how="left")
            j["change"] = (j.quotation - j.prev).round(1)
            st.dataframe(j.sort_values("change", ascending=False), width="stretch")
        else:
            st.info("Only one price snapshot so far — changes appear from the second matchday pull.")
        st.subheader("Ownership vs expected points")
        if not proj.empty:
            ch = alt.Chart(proj[proj.pos != "Head Coach"]).mark_circle().encode(
                x=alt.X("popularity", title="ownership"), y=alt.Y("md_pts", title="expected pts"), color="pos",
                tooltip=["name", "team", "quotation", "md_pts", "popularity"]).interactive().properties(height=380)
            st.altair_chart(ch, width="stretch")

# ------------------------------------------------------------------------------------------
elif page == "Model health":
    st.subheader("Backtest (walk-forward, per round)")
    bt = _csv("backtest_rounds.csv")
    if not bt.empty:
        summ = []
        for r, g in bt.groupby("round"):
            summ.append({"round": r, "n": len(g), "MAE model": (g.model - g.actual_pir).abs().mean(),
                         "MAE season-mean": (g.base_mean - g.actual_pir).abs().mean(), "MAE last-3": (g.base_last3 - g.actual_pir).abs().mean()})
        s = pd.DataFrame(summ).round(2)
        st.dataframe(s, hide_index=True)
        long = s.melt(id_vars=["round", "n"], var_name="estimator", value_name="MAE")
        st.altair_chart(alt.Chart(long).mark_line(point=True).encode(x="round:O", y="MAE:Q", color="estimator:N").properties(height=300), width="stretch")
    rec = _csv("reconcile.csv")
    if not rec.empty:
        st.subheader("Scoring reconciliation (platform vs official)")
        st.write(rec.status.value_counts().to_frame("count").T)
    st.subheader("Last pipeline log")
    st.code(re.sub(r"\x1b\[[0-9;]*m", "", status["log"])[-6000:])
