"""In-round management: Monte Carlo of the swap / captain policy across game nights.

Verified rules (euroleaguebasketball.net, Fantaking rulebook):
- A player's final role sets the multiplier for his whole round score (bench = 50%).
- Between turns, a field player who already played can be demoted; only a player who has NOT
  yet taken the field can be promoted (bench -> starter / sixth man / captain). Positions must
  match (formation may change among 2-2-1, 1-2-2, 2-1-2, 1-3-1, 3-1-1).
- Captain (2x) must be a starter and can be moved to a not-yet-played starter between turns.

Policy simulated here (greedy, one pass per turn boundary):
  swap bench b (not yet played) for field f (already played, same position) when E[b] > S_f,
  move captaincy to the not-yet-played field player with the highest expectation when it exceeds
  the current captain's realised total.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

import numpy as np
import pandas as pd

FIELD_SLOTS = 6  # 5 starters + sixth man


@dataclass
class InRoundPlan:
    static_pts: float
    managed_pts: float
    gain: float
    notes: list[str]


def _games(row) -> list[dict]:
    return json.loads(row.games_json) if isinstance(row.games_json, str) else []


def simulate(squad: pd.DataFrame, n_sims: int = 3000, seed: int = 7) -> InRoundPlan:
    rng = np.random.default_rng(seed)
    players = squad[squad.pos != "Head Coach"].reset_index(drop=True)
    coach = squad[squad.pos == "Head Coach"]
    coach_pts = float(coach.md_pts.sum())
    n = len(players)
    games = [_games(r) for r in players.itertuples()]
    turns = sorted({g["turn"] for gs in games for g in gs}) or [1]
    pos = players.pos.tolist()
    field0 = players.role.isin(["starter", "sixth"]).to_numpy()
    cap0 = int(np.argmax(players.captain.to_numpy())) if players.captain.any() else -1
    exp_total = np.array([sum(g["fp"] for g in gs) for gs in games])

    static_sum, managed_sum = 0.0, 0.0
    swap_counts = np.zeros(n)
    cap_moves = 0
    for _ in range(n_sims):
        # realised score per player per turn
        real = np.zeros((n, len(turns) + 1))
        for i, gs in enumerate(games):
            for g in gs:
                real[i, g["turn"]] = rng.normal(g["fp"], g["sd"])
        total = real.sum(axis=1)
        # static: initial roles
        mult = np.where(field0, 1.0, 0.5)
        if cap0 >= 0:
            mult[cap0] += 1.0
        static_sum += float((total * mult).sum())
        # managed
        field = field0.copy()
        cap = cap0
        played = np.zeros(n, dtype=bool)
        realised = np.zeros(n)
        for t in turns:
            # night t happens
            for i, gs in enumerate(games):
                if any(g["turn"] == t for g in gs):
                    played[i] = True
                    realised[i] += real[i, t]
            if t == turns[-1]:
                break
            # expectation of what remains for each player
            remaining = np.array([sum(g["fp"] for g in gs if g["turn"] > t) for gs in games])
            # swaps: bench not-yet-played vs field already-played, same position
            for b in np.argsort(-exp_total):
                if field[b] or played[b]:
                    continue
                best_f, best_gain = -1, 0.0
                for f in range(n):
                    if not field[f] or not played[f] or pos[f] != pos[b]:
                        continue
                    gain = 0.5 * (exp_total[b] - (realised[f] + remaining[f]))
                    if gain > best_gain:
                        best_f, best_gain = f, gain
                if best_f >= 0:
                    field[b], field[best_f] = True, False
                    swap_counts[b] += 1
                    if cap == best_f:
                        cap = b  # captaincy follows the swap only if b is promotable to starter (it is: not yet played)
            # captain move: to a not-yet-played field player with higher expectation than captain's total
            if cap >= 0 and played[cap]:
                cap_total = realised[cap] + remaining[cap]
                cands = [i for i in range(n) if field[i] and not played[i]]
                if cands:
                    best = max(cands, key=lambda i: exp_total[i])
                    if exp_total[best] > cap_total:
                        cap = best
                        cap_moves += 1
        mult = np.where(field, 1.0, 0.5)
        if cap >= 0:
            mult[cap] += 1.0
        managed_sum += float((total * mult).sum())

    static = static_sum / n_sims + coach_pts
    managed = managed_sum / n_sims + coach_pts
    notes = []
    for i in np.argsort(-swap_counts):
        if swap_counts[i] / n_sims >= 0.15:
            notes.append(f"{players.name.iloc[i]} ({pos[i][0]}, T{players.first_turn.iloc[i]}) is promoted from the bench in {swap_counts[i] / n_sims:.0%} of simulations")
    if cap_moves / n_sims >= 0.15:
        notes.append(f"captaincy is moved after the first night in {cap_moves / n_sims:.0%} of simulations")
    return InRoundPlan(round(static, 1), round(managed, 1), round(managed - static, 1), notes)
