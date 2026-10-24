"""ILP lineup and trade optimiser (PuLP / CBC).

Decision per player: in squad (x), starter (s), sixth man (m), bench (b), captain (c).
Scoring weights verified on the platform: starters, 6th man, coach x1; bench x0.5; captain x2.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import pulp

POS_QUOTA = {"Guard": 4, "Forward": 4, "Center": 2, "Head Coach": 1}
MAX_SAME_CLUB = 6
BENCH_FACTOR = 0.5
FUTURE_FACTOR = 0.75        # average multiplier of a squad player in future matchdays
CAPTAIN_SD_TILT = 0.4       # prefer high-ceiling captains


@dataclass
class Solution:
    squad: pd.DataFrame
    trades_out: list[str]
    trades_in: list[str]
    captain: str
    coach: str
    expected_md_pts: float
    cost: float
    budget: float
    status: str


def optimise(
    proj: pd.DataFrame,
    budget: float,
    prev_ids: set[str],
    max_trades: int = 4,
    mu_price: float = 0.0,
    exp_price_change: dict[str, float] | None = None,
    lock_squad: bool = False,
    keep_ids: set[str] | None = None,
) -> Solution:
    exp_price_change = exp_price_change or {}
    df = proj.copy()
    df = df[df.quotation > 0].reset_index(drop=True)
    ids = list(df.platform_id)
    pos = dict(zip(df.platform_id, df.pos))
    club = dict(zip(df.platform_id, df.team))
    q = dict(zip(df.platform_id, df.quotation))
    md = dict(zip(df.platform_id, df.md_pts))
    sd = dict(zip(df.platform_id, df.md_sd))
    fut = {i: max(h - m_, 0.0) for i, h, m_ in zip(df.platform_id, df.horizon_pts, df.md_pts)}
    players = [i for i in ids if pos[i] != "Head Coach"]
    coaches = [i for i in ids if pos[i] == "Head Coach"]

    prob = pulp.LpProblem("elfa", pulp.LpMaximize)
    def _bin(prefix: str, keys: list[str]) -> dict[str, pulp.LpVariable]:
        return {k: pulp.LpVariable(f"{prefix}_{k}", cat="Binary") for k in keys}

    x, s, m, b, c = _bin("x", ids), _bin("s", players), _bin("m", players), _bin("b", players), _bin("c", players)

    prob += (
        pulp.lpSum((s[i] + m[i]) * md[i] + BENCH_FACTOR * b[i] * md[i] + c[i] * (md[i] + CAPTAIN_SD_TILT * sd[i]) for i in players)
        + pulp.lpSum(x[i] * md[i] for i in coaches)
        + pulp.lpSum(x[i] * FUTURE_FACTOR * fut[i] for i in ids)
        + mu_price * pulp.lpSum(x[i] * exp_price_change.get(i, 0.0) for i in ids)
    )

    for p_, n in POS_QUOTA.items():
        prob += pulp.lpSum(x[i] for i in ids if pos[i] == p_) == n
    for i in players:
        prob += s[i] + m[i] + b[i] == x[i]
        prob += c[i] <= s[i]
    prob += pulp.lpSum(s[i] for i in players) == 5
    prob += pulp.lpSum(m[i] for i in players) == 1
    prob += pulp.lpSum(b[i] for i in players) == 4
    prob += pulp.lpSum(c[i] for i in players) == 1
    # starting five must be a legal formation: at least one and at most three of each position
    for p_ in ("Guard", "Forward", "Center"):
        prob += pulp.lpSum(s[i] for i in players if pos[i] == p_) >= 1
        prob += pulp.lpSum(s[i] for i in players if pos[i] == p_) <= 3
    for cl in set(club.values()):
        prob += pulp.lpSum(x[i] for i in ids if club[i] == cl) <= MAX_SAME_CLUB
    prob += pulp.lpSum(x[i] * q[i] for i in ids) <= budget
    # trades: new players <= 4, or 3 if the coach also changes
    new_players = pulp.lpSum(x[i] for i in players if i not in prev_ids)
    new_coach = pulp.lpSum(x[i] for i in coaches if i not in prev_ids)
    if lock_squad:
        for i in ids:
            prob += x[i] == (1 if i in prev_ids else 0)
    else:
        prob += new_players + new_coach <= max_trades
        for i in (keep_ids or set()):
            if i in x:
                prob += x[i] == 1
    prob.solve(pulp.PULP_CBC_CMD(msg=False, timeLimit=60))
    status = pulp.LpStatus[prob.status]

    chosen = [i for i in ids if x[i].value() and x[i].value() > 0.5]
    role = {}
    for i in players:
        if s[i].value() and s[i].value() > 0.5:
            role[i] = "starter"
        elif m[i].value() and m[i].value() > 0.5:
            role[i] = "sixth"
        elif b[i].value() and b[i].value() > 0.5:
            role[i] = "bench"
    for i in coaches:
        role[i] = "coach"
    cap = next((i for i in players if c[i].value() and c[i].value() > 0.5), None)
    squad = df[df.platform_id.isin(chosen)].copy()
    squad["role"] = squad.platform_id.map(role)
    squad["captain"] = squad.platform_id == cap
    order = {"starter": 0, "sixth": 1, "bench": 2, "coach": 3}
    squad = squad.sort_values(["role", "md_pts"], key=lambda col: col.map(order) if col.name == "role" else -col).reset_index(drop=True)
    mult = squad.role.map({"starter": 1, "sixth": 1, "bench": BENCH_FACTOR, "coach": 1}) + squad.captain.astype(int)
    expected = float((squad.md_pts * mult).sum())
    names = dict(zip(df.platform_id, df.name))
    return Solution(
        squad=squad,
        trades_out=[names.get(i, i) for i in prev_ids if i not in chosen and i in names],
        trades_in=[names[i] for i in chosen if i not in prev_ids],
        captain=names.get(cap, "?"),
        coach=next((names[i] for i in chosen if pos[i] == "Head Coach"), "?"),
        expected_md_pts=round(expected, 1),
        cost=round(float(squad.quotation.sum()), 1),
        budget=budget,
        status=status,
    )
