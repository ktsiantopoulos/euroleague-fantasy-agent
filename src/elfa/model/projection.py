"""Per-player projection for the current matchday and a rolling horizon.

projected game PIR = minutes_hat x rate_hat x home factor x pace factor + DvP matchup term
projected fantasy  = p_play x PIR x (1 + WIN_BONUS x p_win)       (platform scoring)
Coaches: expected margin-bucket points.

All parameters live in `Params` so the backtest can grid-search them.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from elfa.model.teams import Game, coach_ev, margin_mu, win_prob

WIN_BONUS = 0.10


@dataclass
class Params:
    w_minutes: tuple[float, float, float] = (0.2, 0.3, 0.5)   # last, mean3, mean5 (grid, R4-7)
    rate_prior_minutes: float = 40.0                           # shrinkage toward league PIR/min
    lam_recent: float = 0.6                                    # weight of last-5 rate vs season rate
    eta_home: float = 0.04
    gamma_dvp: float = 1.0                                     # grid, R4-7
    sd_prior_games: float = 4.0
    horizon_weights: tuple[float, ...] = (1.0, 0.6, 0.3)
    dnp_recent_penalty: float = 0.5                            # multiply minutes if last game was a DNP
    minutes_sample_prior: float = 0.5                          # n/(n+0.5): 1 game -> 0.67, 7 games -> 0.93
    flags: dict = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path | None = None) -> Params:
        """Current tuned parameters (data/processed/params.json), falling back to the defaults."""
        from elfa.config import PROCESSED

        path = path or PROCESSED / "params.json"
        if path.exists():
            d = json.loads(path.read_text(encoding="utf-8"))
            d.pop("adopted_at", None); d.pop("note", None)
            d = {k: (tuple(v) if isinstance(v, list) else v) for k, v in d.items() if k in cls.__dataclass_fields__}
            return cls(**d)
        return cls()

    def save(self, note: str, path: Path | None = None) -> None:
        from elfa.config import PROCESSED

        path = path or PROCESSED / "params.json"
        d = asdict(self); d["note"] = note
        path.write_text(json.dumps(d, indent=1), encoding="utf-8")


def _player_form(pg: pd.DataFrame, league_rate: float, league_sd: float, p: Params) -> pd.DataFrame:
    """One row per person code with minutes_hat, rate_hat, sd, n_games, last_minutes."""
    rows = []
    for code, g in pg.sort_values("date_utc").groupby("player_code"):
        mins = g.minutes.to_numpy()
        pirs = g.pir.to_numpy()
        n = len(mins)
        last, m3, m5 = mins[-1], mins[-3:].mean(), mins[-5:].mean()
        w1, w3, w5 = p.w_minutes
        min_hat = w1 * last + w3 * m3 + w5 * m5
        if last == 0 and n >= 2:
            min_hat *= p.dnp_recent_penalty
        min_hat *= n / (n + p.minutes_sample_prior)   # small samples: discount toward 0
        tot_min, tot_pir = mins.sum(), pirs.sum()
        rate_season = (tot_pir + p.rate_prior_minutes * league_rate) / (tot_min + p.rate_prior_minutes)
        m5s, p5s = mins[-5:].sum(), pirs[-5:].sum()
        rate_recent = (p5s + p.rate_prior_minutes * league_rate) / (m5s + p.rate_prior_minutes)
        rate_hat = p.lam_recent * rate_recent + (1 - p.lam_recent) * rate_season
        sd = pirs.std(ddof=0) if n > 1 else league_sd
        sd = (n * sd + p.sd_prior_games * league_sd) / (n + p.sd_prior_games)
        rows.append((code, min_hat, rate_hat, sd, n, last, g.team.iloc[-1], float(g.starter.iloc[-1])))
    return pd.DataFrame(rows, columns=["person_code", "min_hat", "rate_hat", "sd", "n_games", "last_min", "team_off", "last_starter"])


def project(
    market: list[dict],
    roster_ids: set[str],
    pg: pd.DataFrame,
    player_map: pd.DataFrame,
    team_map: pd.DataFrame,
    dvp: pd.DataFrame,
    ratings: pd.DataFrame,
    horizon: list[list[Game]],
    odds: dict | None = None,
    p: Params | None = None,
) -> pd.DataFrame:
    p = p or Params.load()
    odds = odds or {}
    played = pg[pg.played]
    league_rate = played.pir.sum() / played.minutes.sum()
    league_sd = played.pir.std()
    pos_minutes = played.groupby(["game_code", "team", "fpos"]).minutes.sum().groupby("fpos").mean().to_dict()
    form = _player_form(pg, league_rate, league_sd, p).set_index("person_code")
    t2o = dict(zip(team_map.platform_abbr, team_map.official_code))
    p2o = dict(zip(player_map.platform_id.astype(str), player_map.person_code))
    dvp_idx = dvp.set_index(["team", "fpos"]).piroe_shrunk.to_dict()
    r = ratings.set_index("team")
    league_pace = r.pace.mean()

    def game_context(team: str, g: Game) -> tuple[float, float, bool, str]:
        home = g.home == team
        opp = g.away if home else g.home
        mu = margin_mu(g.home, g.away, ratings)
        o = odds.get((g.home, g.away))
        if o and o.get("home_spread") is not None:
            mu = -o["home_spread"]
        pw = o["home_win_prob"] if o and o.get("home_win_prob") is not None else win_prob(mu)
        if not home:
            mu, pw = -mu, 1 - pw
        return mu, pw, home, opp

    # turn index = order of game night within the current matchday (1 = first night)
    nights = sorted({g.date_utc[:10] for g in horizon[0]})
    turn_of = {d: i + 1 for i, d in enumerate(nights)}

    rows = []
    for m in market:
        pid = str(m["id"])
        pos = (m.get("position") or {}).get("name")
        team_pl = (m.get("team") or {}).get("abbreviation")
        team = t2o.get(team_pl)
        prob_play = float(m.get("probability_of_playing") if m.get("probability_of_playing") is not None else 1.0)
        if m.get("is_injured") and prob_play >= 1.0:
            prob_play = 0.25
        code = p2o.get(pid)
        f = form.loc[code] if isinstance(code, str) and code in form.index else None
        flags = []
        why = []
        games_detail = []
        md_pts, md_var, horizon_pts, games_md = 0.0, 0.0, 0.0, 0
        min_hat = rate_hat = 0.0
        if pos == "Head Coach":
            for h_i, games in enumerate(horizon):
                for g in games:
                    if team not in (g.home, g.away):
                        continue
                    mu, pw, home, opp = game_context(team, g)
                    ev = coach_ev(mu)
                    horizon_pts += p.horizon_weights[h_i] * ev
                    if h_i == 0:
                        md_pts += ev
                        md_var += 12.0 ** 2
                        games_md += 1
                        games_detail.append({"turn": turn_of.get(g.date_utc[:10], 1), "opp": opp, "home": home, "fp": round(ev, 2), "sd": 12.0, "pw": round(pw, 3)})
                        why.append(f"{'vs' if home else '@'} {opp}: margin {mu:+.0f}, win {pw:.0%} → EV {ev:+.1f}")
            flags.append("coach")
        else:
            if f is None:
                flags.append("no games this season")
            else:
                min_hat, rate_hat = float(f.min_hat), float(f.rate_hat)
                if f.n_games < 3:
                    flags.append(f"only {int(f.n_games)} game(s)")
                if f.last_min == 0:
                    flags.append("DNP last game")
            for h_i, games in enumerate(horizon):
                for g in games:
                    if team not in (g.home, g.away) or f is None:
                        continue
                    mu, pw, home, opp = game_context(team, g)
                    pace_f = ((r.pace.get(team, league_pace) + r.pace.get(opp, league_pace)) / 2) / league_pace
                    pir = min_hat * rate_hat * (1 + p.eta_home if home else 1 - p.eta_home) * pace_f
                    share = min_hat / max(pos_minutes.get(pos, 80.0), 1.0)
                    pir += p.gamma_dvp * share * dvp_idx.get((opp, pos), 0.0)
                    fp = prob_play * pir * (1 + WIN_BONUS * pw)
                    horizon_pts += p.horizon_weights[h_i] * fp
                    if h_i == 0:
                        dv = dvp_idx.get((opp, pos), 0.0)
                        g_sd = float(np.sqrt((prob_play * float(f.sd)) ** 2 + (pir ** 2) * prob_play * (1 - prob_play)))
                        games_detail.append({"turn": turn_of.get(g.date_utc[:10], 1), "opp": opp, "home": home, "fp": round(fp, 2), "sd": round(g_sd, 2), "pw": round(pw, 3)})
                        why.append(f"T{turn_of.get(g.date_utc[:10], 1)} {'vs' if home else '@'} {opp} (DvP {dv:+.1f}, win {pw:.0%}) → {fp:.1f}")
                        md_pts += fp
                        md_var += (prob_play * float(f.sd)) ** 2 + (pir ** 2) * prob_play * (1 - prob_play)
                        games_md += 1
        if games_md == 0 and pos != "Head Coach":
            flags.append("no game this matchday")
        if f is not None and pos != "Head Coach":
            trend = "starter" if f.last_starter else "bench"
            why.insert(0, f"{min_hat:.0f} min proj ({trend}, last {f.last_min:.0f}), {rate_hat:.2f} PIR/min over {int(f.n_games)} g")
        rows.append(
            {
                "platform_id": pid, "name": f"{m.get('first_name','')} {m.get('last_name','')}".strip(),
                "pos": pos, "team": team_pl, "team_off": team, "quotation": float(m["quotation"]),
                "avg_pts_platform": m.get("avg_pts"), "popularity": m.get("popularity"),
                "prob_play": prob_play, "min_hat": round(min_hat, 1), "rate_hat": round(rate_hat, 3),
                "games_md": games_md, "md_pts": round(md_pts, 2), "md_sd": round(float(np.sqrt(md_var)), 2),
                "md_p90": round(md_pts + 1.2816 * float(np.sqrt(md_var)), 2),
                "horizon_pts": round(horizon_pts, 2),
                "value": round(md_pts / float(m["quotation"]), 3) if float(m["quotation"]) > 0 else 0.0,
                "in_roster": pid in roster_ids, "flags": "; ".join(flags), "why": " · ".join(why),
                "first_turn": min((d["turn"] for d in games_detail), default=99),
                "games_json": json.dumps(games_detail),
            }
        )
    return pd.DataFrame(rows)
