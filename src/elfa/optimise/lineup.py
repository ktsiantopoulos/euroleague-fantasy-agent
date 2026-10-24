"""ILP lineup and trade optimiser (PuLP / CBC).

Decision per player: in squad (x), starter (s), sixth man (m), bench (b), captain (c).
Scoring weights verified on the platform: starters, 6th man, coach x1; bench x0.5; captain x2.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd
import pulp

POS_QUOTA = {"Guard": 4, "Forward": 4, "Center": 2, "Head Coach": 1}
MAX_SAME_CLUB = 6
BENCH_FACTOR = 0.5
FUTURE_FACTOR = 0.75        # average multiplier of a squad player in future matchdays
CAPTAIN_SD_TILT = 0.4       # prefer high-ceiling captains
MIN_PROMOTABLE_BENCH = 2    # bench players whose first game is after night 1 (swap options)
MIN_FIRST_NIGHT_FIELD = 3   # field players who play on night 1 (information before the swap window)
SOFT_CLUB_CAP = 3           # top-100 managers hold at most 2-3 per club; each player above this costs ...
CLUB_CAP_PENALTY = 3.0      # ... this many expected points in the objective
BENCH_OPTION_WEIGHT = 1.0   # weight of the promotion option (0.5 = my conservative sim; elite promote ~35% of field slots)
BENCH_PRICE_FLOOR = 6.0     # top-100 bench averages 7.4 credits; each credit below this costs ...
BENCH_FLOOR_PENALTY = 1.0   # ... this many expected points


def _pos_part(mu: float, sd: float) -> float:
    """E[max(X,0)] for X ~ N(mu, sd)."""
    if sd <= 0:
        return max(mu, 0.0)
    z = mu / sd
    return sd * math.exp(-0.5 * z * z) / math.sqrt(2 * math.pi) + mu * 0.5 * (1 + math.erf(z / math.sqrt(2)))


def bench_value(df: pd.DataFrame) -> dict[str, float]:
    """Expected contribution of each player if he sits on the bench: 50% of his points plus the
    option of being promoted after night 1 in place of a same-position field player who has played.
    The reference field player is the average of the top-3 first-night players at that position."""
    out = {}
    first = df[(df.first_turn == 1) & (df.pos != "Head Coach")]
    ref = {p_: first[first.pos == p_].nlargest(3, "md_pts")[["md_pts", "md_sd"]] for p_ in ("Guard", "Forward", "Center")}
    for r in df.itertuples():
        base = BENCH_FACTOR * r.md_pts
        prem = 0.0
        if r.pos != "Head Coach" and r.first_turn >= 2 and len(ref.get(r.pos, [])):
            prem = BENCH_OPTION_WEIGHT * 0.5 * float(sum(_pos_part(r.md_pts - f.md_pts, f.md_sd) for f in ref[r.pos].itertuples()) / len(ref[r.pos]))
        out[r.platform_id] = base + prem
    return out


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
    balance: bool = True,
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
    if "first_turn" not in df:
        df["first_turn"] = 1
    bval = bench_value(df)
    ft = dict(zip(df.platform_id, df.first_turn))
    fut = {i: max(h - m_, 0.0) for i, h, m_ in zip(df.platform_id, df.horizon_pts, df.md_pts)}
    players = [i for i in ids if pos[i] != "Head Coach"]
    coaches = [i for i in ids if pos[i] == "Head Coach"]

    prob = pulp.LpProblem("elfa", pulp.LpMaximize)
    def _bin(prefix: str, keys: list[str]) -> dict[str, pulp.LpVariable]:
        return {k: pulp.LpVariable(f"{prefix}_{k}", cat="Binary") for k in keys}

    x, s, m, b, c = _bin("x", ids), _bin("s", players), _bin("m", players), _bin("b", players), _bin("c", players)

    clubs = sorted(set(club.values()))
    over = {cl: pulp.LpVariable(f"over_{k}", lowBound=0) for k, cl in enumerate(clubs)}
    prob += (
        pulp.lpSum((s[i] + m[i]) * md[i] + b[i] * bval[i] + c[i] * (md[i] + CAPTAIN_SD_TILT * sd[i]) for i in players)
        + pulp.lpSum(x[i] * md[i] for i in coaches)
        + pulp.lpSum(x[i] * FUTURE_FACTOR * fut[i] for i in ids)
        + mu_price * pulp.lpSum(x[i] * exp_price_change.get(i, 0.0) for i in ids)
        - CLUB_CAP_PENALTY * pulp.lpSum(over[cl] for cl in clubs)
        - BENCH_FLOOR_PENALTY * pulp.lpSum(b[i] * max(BENCH_PRICE_FLOOR - q[i], 0.0) for i in players)
    )
    for cl in clubs:
        prob += over[cl] >= pulp.lpSum(x[i] for i in ids if club[i] == cl) - SOFT_CLUB_CAP

    for p_, n in POS_QUOTA.items():
        prob += pulp.lpSum(x[i] for i in ids if pos[i] == p_) == n
    for i in players:
        prob += s[i] + m[i] + b[i] == x[i]
        prob += c[i] <= s[i]
    prob += pulp.lpSum(s[i] for i in players) == 5
    prob += pulp.lpSum(m[i] for i in players) == 1
    prob += pulp.lpSum(b[i] for i in players) == 4
    prob += pulp.lpSum(c[i] for i in players) == 1
    # starting five must be a legal formation (2-2-1, 1-2-2, 2-1-2, 1-3-1, 3-1-1): 1-3 of each position
    for p_ in ("Guard", "Forward", "Center"):
        prob += pulp.lpSum(s[i] for i in players if pos[i] == p_) >= 1
        prob += pulp.lpSum(s[i] for i in players if pos[i] == p_) <= 3
    # house rule: never a center as sixth man
    for i in players:
        if pos[i] == "Center":
            prob += m[i] == 0
    # balance across game nights (only meaningful when the matchday has more than one night)
    multi_night = any(v >= 2 for v in ft.values() if v < 99)
    if multi_night and balance:
        prob += pulp.lpSum(b[i] for i in players if 2 <= ft[i] < 99) >= MIN_PROMOTABLE_BENCH
        prob += pulp.lpSum(s[i] + m[i] for i in players if ft[i] == 1) >= MIN_FIRST_NIGHT_FIELD
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
    if status != "Optimal" and balance:
        return optimise(proj, budget, prev_ids, max_trades, mu_price, exp_price_change, lock_squad, keep_ids, balance=False)

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
    status = status + ("" if balance else " (night-balance relaxed)")
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
