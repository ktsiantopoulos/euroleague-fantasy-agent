"""Thin bridge so the report module does not import pulp at module load time."""
from __future__ import annotations

import pandas as pd

from elfa.optimise.lineup import Solution, optimise


def run_optimiser(proj: pd.DataFrame, budget: float, prev_ids: set[str], max_trades: int,
                  mu_price: float = 0.0, lock_squad: bool = False, keep_ids: set[str] | None = None) -> Solution:
    return optimise(proj, budget, prev_ids, max_trades=max_trades, mu_price=mu_price, lock_squad=lock_squad, keep_ids=keep_ids)
