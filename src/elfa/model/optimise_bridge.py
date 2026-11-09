"""Thin bridge so the report module does not import pulp at module load time."""
from __future__ import annotations

import pandas as pd

from elfa.optimise.lineup import Solution, optimise


def run_optimiser(proj: pd.DataFrame, budget: float, prev_ids: set[str], max_trades: int,
                  mu_price: float | None = None, lock_squad: bool = False, keep_ids: set[str] | None = None,
                  balance: bool = True, exp_price_change: dict[str, float] | None = None) -> Solution:
    return optimise(proj, budget, prev_ids, max_trades=max_trades, mu_price=mu_price, exp_price_change=exp_price_change,
                    lock_squad=lock_squad, keep_ids=keep_ids, balance=balance)
