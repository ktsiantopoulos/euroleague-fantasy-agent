"""Team context, player usage and fixture difficulty — this season's box scores only.

team_context : per club, per-game "for" and "allowed" box-score environment (possessions, FGA, 2PA/3PA/FTA,
               rebounds, assists, turnovers, PIR, points, eFG%, TS%), 0-100 percentile scores and a defence
               weakness score; FDR 1 (easy) - 5 (hard) is how hard it is to score fantasy points against the club.
usage        : per player shot share (player FGA/G ÷ team FGA/G), FGA per minute / per 40, 2PA/3PA/FTA per minute,
               fouls drawn and blocks against per game, and last-3 vs season deltas as a role-change signal.
fixture_fdr  : per club, the next N games with the opponent's FDR adjusted for venue and win probability.
"""
from __future__ import annotations

import pandas as pd

from elfa.config import PROCESSED
from elfa.model.teams import margin_mu, win_prob

FDR_HOME_ADJ = 0.3        # away games are harder for fantasy production (minutes, fouls, PIR)
FDR_WIN_ADJ = 1.0         # +/- for win probability (the 10% bonus and garbage time both follow it)
ALLOWED_WEIGHTS = {"pir_allowed": 0.40, "pts_allowed": 0.20, "pace": 0.20, "fga_allowed": 0.10, "reb_allowed": 0.10}


def _team_games(pg: pd.DataFrame) -> pd.DataFrame:
    g = pg[pg.played].groupby(["game_code", "team", "opponent", "home"], as_index=False).agg(
        pts=("pts", "sum"), fg2m=("fg2m", "sum"), fg2a=("fg2a", "sum"), fg3m=("fg3m", "sum"), fg3a=("fg3a", "sum"),
        ftm=("ftm", "sum"), fta=("fta", "sum"), oreb=("oreb", "sum"), dreb=("dreb", "sum"), reb=("reb", "sum"),
        ast=("ast", "sum"), stl=("stl", "sum"), tov=("tov", "sum"), blk=("blk", "sum"), pir=("pir", "sum"),
        fd=("fd", "sum"), pf=("pf", "sum"), minutes=("minutes", "sum"))
    g["fga"] = g.fg2a + g.fg3a
    g["fgm"] = g.fg2m + g.fg3m
    g["poss"] = g.fga + 0.44 * g.fta - g.oreb + g.tov
    g["efg"] = (g.fgm + 0.5 * g.fg3m) / g.fga.clip(lower=1)
    g["ts"] = g.pts / (2 * (g.fga + 0.44 * g.fta)).clip(lower=1)
    return g


def _pct_score(s: pd.Series) -> pd.Series:
    return (s.rank(pct=True) * 100).round(0)


def team_context(pg: pd.DataFrame) -> pd.DataFrame:
    tg = _team_games(pg)
    stats = ["pts", "fga", "fg2a", "fg3a", "fta", "oreb", "dreb", "reb", "ast", "stl", "tov", "blk", "pir", "poss", "efg", "ts"]
    # allowed = what the opponent produced in the same game
    opp = tg[["game_code", "team", *stats]].rename(columns={"team": "opponent", **{s: f"{s}_allowed" for s in stats}})
    both = tg.merge(opp, on=["game_code", "opponent"], how="left")
    agg = {s: (s, "mean") for s in stats} | {f"{s}_allowed": (f"{s}_allowed", "mean") for s in stats}
    ctx = both.groupby("team").agg(games=("game_code", "nunique"), **agg).reset_index()
    ctx["pace"] = (ctx.poss + ctx.poss_allowed) / 2
    ctx["pace_score"] = _pct_score(ctx.pace)
    for s in ("pir", "pts", "fga", "reb"):
        ctx[f"{s}_allowed_score"] = _pct_score(ctx[f"{s}_allowed"])
    ctx["defence_weakness_score"] = ctx[["pir_allowed_score", "pts_allowed_score", "fga_allowed_score", "reb_allowed_score"]].mean(axis=1).round(0)
    ease = (ALLOWED_WEIGHTS["pir_allowed"] * ctx.pir_allowed_score + ALLOWED_WEIGHTS["pts_allowed"] * ctx.pts_allowed_score
            + ALLOWED_WEIGHTS["pace"] * ctx.pace_score + ALLOWED_WEIGHTS["fga_allowed"] * ctx.fga_allowed_score
            + ALLOWED_WEIGHTS["reb_allowed"] * ctx.reb_allowed_score)
    ctx["matchup_ease"] = ease.round(0)                       # 100 = easiest club to score fantasy points against
    ctx["fdr"] = (5 - 4 * ease / 100).round(2)                # 1 easy .. 5 hard
    num = ctx.select_dtypes("number").columns
    ctx[num] = ctx[num].round(3)
    return ctx.sort_values("fdr").reset_index(drop=True)


def usage(pg: pd.DataFrame) -> pd.DataFrame:
    p = pg[pg.played & (pg.minutes > 0)].copy()
    p["fga"] = p.fg2a + p.fg3a
    team_fga = _team_games(pg).groupby("team").fga.mean().rename("team_fga_pg")
    p = p.sort_values("date_utc")
    rows = []
    for code, g in p.groupby("player_code"):
        last3 = g.tail(3)
        mins, m3 = g.minutes.sum(), last3.minutes.sum()
        team = g.team.iloc[-1]
        row = {
            "player_code": code, "player_name": g.player_name.iloc[-1], "team": team, "games": len(g),
            "min_pg": g.minutes.mean(), "fga_pg": g.fga.mean(), "team_fga_pg": team_fga.get(team),
            "fga_per_min": g.fga.sum() / mins if mins else 0.0, "fga_per40": 40 * g.fga.sum() / mins if mins else 0.0,
            "fg2a_per_min": g.fg2a.sum() / mins if mins else 0.0, "fg3a_per_min": g.fg3a.sum() / mins if mins else 0.0,
            "fta_per_min": g.fta.sum() / mins if mins else 0.0,
            "fd_pg": g.fd.mean(), "blka_pg": g.blk_against.mean(), "pf_pg": g.pf.mean(),
            "min_last3": last3.minutes.mean(), "fga_per_min_last3": last3.fga.sum() / m3 if m3 else 0.0,
            "starts": int(g.starter.sum()), "starter_last": bool(g.starter.iloc[-1]),
        }
        row["shot_share"] = 100 * row["fga_pg"] / row["team_fga_pg"] if row["team_fga_pg"] else None
        row["usage_delta_last3"] = row["fga_per_min_last3"] - row["fga_per_min"]
        row["min_delta_last3"] = row["min_last3"] - row["min_pg"]
        rows.append(row)
    u = pd.DataFrame(rows)
    if u.empty:
        return u
    # role-change signal: more shots per minute AND more minutes lately, or a clear drop in both
    u["role_signal"] = ""
    u.loc[(u.usage_delta_last3 >= 0.08) & (u.min_delta_last3 >= 3) & (u.games >= 4), "role_signal"] = "rising"
    u.loc[(u.usage_delta_last3 <= -0.08) & (u.min_delta_last3 <= -3) & (u.games >= 4), "role_signal"] = "falling"
    num = u.select_dtypes("number").columns
    u[num] = u[num].round(3)
    return u.sort_values("shot_share", ascending=False).reset_index(drop=True)


def fixture_fdr(schedule: list[dict], ctx: pd.DataFrame, ratings: pd.DataFrame, odds: dict | None = None,
                from_round: int | None = None, n_games: int = 5) -> pd.DataFrame:
    """Next `n_games` per club with an FDR per game: opponent FDR ± venue ± win probability, clipped to 1-5."""
    odds = odds or {}
    fdr_of = dict(zip(ctx.team, ctx.fdr))
    ease_of = dict(zip(ctx.team, ctx.matchup_ease))
    played = {g["round"] for g in schedule if g.get("played")}
    start = from_round or (max(played) + 1 if played else 1)
    rs = sorted((g for g in schedule if g["phaseType"]["code"] == "RS" and g["round"] >= start and not g.get("played")),
                key=lambda g: g["utcDate"])
    rows = []
    for g in rs:
        h, a = g["local"]["club"]["code"], g["road"]["club"]["code"]
        mu = margin_mu(h, a, ratings)
        o = odds.get((h, a))
        if o and o.get("home_spread") is not None:
            mu = -o["home_spread"]
        pw_home = o["home_win_prob"] if o and o.get("home_win_prob") is not None else win_prob(mu)
        for team, opp, home, pw in ((h, a, True, pw_home), (a, h, False, 1 - pw_home)):
            base = fdr_of.get(opp, 3.0)
            fdr = base + (-FDR_HOME_ADJ if home else FDR_HOME_ADJ) + FDR_WIN_ADJ * (0.5 - pw)
            rows.append({"team": team, "round": g["round"], "game_code": g["gameCode"], "date_utc": g["utcDate"],
                         "opponent": opp, "home": home, "opp_fdr": base, "opp_ease": ease_of.get(opp),
                         "win_prob": round(pw, 3), "fdr": round(min(5.0, max(1.0, fdr)), 2),
                         "odds": bool(o and o.get("home_win_prob") is not None)})
    f = pd.DataFrame(rows)
    if f.empty:
        return f
    f["n"] = f.groupby("team").cumcount() + 1
    f = f[f.n <= n_games].copy()
    f["next_n_avg"] = f.groupby("team").fdr.transform("mean").round(2)
    return f.sort_values(["team", "n"]).reset_index(drop=True)


def write_context(pg: pd.DataFrame, schedule: list[dict], ratings: pd.DataFrame, odds: dict | None = None,
                  from_round: int | None = None) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    ctx = team_context(pg)
    u = usage(pg)
    f = fixture_fdr(schedule, ctx, ratings, odds, from_round)
    ctx.to_csv(PROCESSED / "team_context.csv", index=False)
    u.to_csv(PROCESSED / "usage.csv", index=False)
    f.to_csv(PROCESSED / "fdr.csv", index=False)
    return ctx, u, f
