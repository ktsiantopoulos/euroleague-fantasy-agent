"""Walk-forward backtest of the game-level PIR projection (P1 gate).

For each round r in `rounds`: fit features on rounds < r, project every player who dressed in
round r, compare to actual. Baselines: season-to-date mean PIR and last-3 mean PIR.
Reports MAE and the correlation with actual, overall and for players with >= 15 projected min.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from elfa.features.dvp import compute_dvp
from elfa.model.projection import Params, _player_form, bias_factor
from elfa.model.teams import margin_mu, team_ratings, win_prob


@dataclass
class BacktestResult:
    table: pd.DataFrame
    summary: pd.DataFrame


def _project_round(train: pd.DataFrame, test: pd.DataFrame, schedule: list[dict], p: Params) -> pd.DataFrame:
    played = train[train.played]
    league_rate = played.pir.sum() / played.minutes.sum()
    league_sd = played.pir.std()
    pos_minutes = played.groupby(["game_code", "team", "fpos"]).minutes.sum().groupby("fpos").mean().to_dict()
    form = _player_form(train, league_rate, league_sd, p).set_index("person_code")
    dvp, _ = compute_dvp(train)
    dvp_idx = dvp.set_index(["team", "fpos"]).piroe_shrunk.to_dict()
    ratings = team_ratings(train, schedule)
    r = ratings.set_index("team")
    league_pace = r.pace.mean()
    rows = []
    for g in test.itertuples():
        if g.player_code not in form.index:
            continue
        f = form.loc[g.player_code]
        home_team, away_team = (g.team, g.opponent) if g.home else (g.opponent, g.team)
        mu = margin_mu(home_team, away_team, ratings)
        pw = win_prob(mu) if g.home else 1 - win_prob(mu)
        pace_f = ((r.pace.get(g.team, league_pace) + r.pace.get(g.opponent, league_pace)) / 2) / league_pace
        pir = f.min_hat * f.rate_hat * (1 + p.eta_home if g.home else 1 - p.eta_home) * pace_f
        pir += p.gamma_dvp * (f.min_hat / max(pos_minutes.get(g.fpos, 80.0), 1.0)) * dvp_idx.get((g.opponent, g.fpos), 0.0)
        pir *= bias_factor(p, g.fpos, f.min_hat)
        hist = train[train.player_code == g.player_code].sort_values("date_utc").pir
        rows.append({
            "round": g.round, "player_code": g.player_code, "player_name": g.player_name, "team": g.team,
            "actual_pir": g.pir, "actual_min": g.minutes,
            "model": pir, "model_fp": pir * (1 + 0.10 * pw),
            "base_mean": hist.mean(), "base_last3": hist.tail(3).mean(),
            "min_hat": f.min_hat, "n_games": f.n_games, "fpos": g.fpos, "rate_hat": f.rate_hat,
            "sd": float(f.sd) * p.sd_scale, "date_utc": g.date_utc,
        })
    return pd.DataFrame(rows)


def backtest(pg: pd.DataFrame, schedule: list[dict], rounds: list[int], p: Params | None = None) -> BacktestResult:
    p = p or Params.load()
    parts = []
    for rnd in rounds:
        train = pg[pg["round"] < rnd]
        test = pg[(pg["round"] == rnd) & (pg.minutes >= 0)]
        if train.empty or test.empty:
            continue
        parts.append(_project_round(train, test, schedule, p))
    table = pd.concat(parts, ignore_index=True)

    def _metrics(df: pd.DataFrame, label: str) -> dict:
        out = {"subset": label, "n": len(df)}
        for col in ("model", "base_mean", "base_last3"):
            out[f"mae_{col}"] = round((df[col] - df.actual_pir).abs().mean(), 2)
            out[f"corr_{col}"] = round(np.corrcoef(df[col], df.actual_pir)[0, 1], 3) if len(df) > 2 else np.nan
        return out

    summary = pd.DataFrame([
        _metrics(table, "all dressed players"),
        _metrics(table[table.min_hat >= 15], "projected >= 15 min"),
        _metrics(table[table.n_games >= 3], ">= 3 prior games"),
    ])
    return BacktestResult(table, summary)


def grid_search(pg: pd.DataFrame, schedule: list[dict], rounds: list[int]) -> pd.DataFrame:
    """Small grid over the three parameters that matter most; scored on MAE for >= 15 projected min."""
    rows = []
    for w in [(0.5, 0.3, 0.2), (0.3, 0.4, 0.3), (0.2, 0.3, 0.5)]:
        for lam in (0.3, 0.6, 0.8):
            for gamma in (0.0, 0.6, 1.0):
                p = Params(w_minutes=w, lam_recent=lam, gamma_dvp=gamma)
                res = backtest(pg, schedule, rounds, p)
                s = res.summary.set_index("subset")
                rows.append({"w_minutes": w, "lam_recent": lam, "gamma_dvp": gamma,
                             "mae_all": s.loc["all dressed players", "mae_model"],
                             "mae_15min": s.loc["projected >= 15 min", "mae_model"],
                             "corr_15min": s.loc["projected >= 15 min", "corr_model"]})
    return pd.DataFrame(rows).sort_values("mae_15min")
