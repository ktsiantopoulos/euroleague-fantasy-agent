"""Which squad the optimiser starts from, and how many trades it may make.

The platform exposes two squads for the current matchday:

* ``roster.json``        - the *pending* squad: what is selected right now, trades included. Every trade in it is
                           reversible until the matchday deadline (first tip-off), so ``team_matchday.trades`` is a
                           count of pending changes, not of spent ones.
* ``roster_locked.json`` - the squad the platform last locked (previous matchday). This is the real baseline:
                           the pending squad may differ from it by at most ``max_num_trades_per_matchday`` players.

Before the deadline the optimiser therefore starts from the locked squad with the full allowance; after it, the
pending squad is locked and no trade is possible.
"""
from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Baseline:
    ids: set[str]                      # squad the optimiser may trade away from
    trades_left: int                   # trades allowed vs `ids`
    pending_ids: set[str]              # squad selected on the platform right now
    locked_ids: set[str]               # squad the platform last locked (empty if unknown)
    open: bool                         # trade window still open
    max_trades: int
    pending_trades: int                # platform's `trades` counter (pending changes vs locked)
    note: str = ""
    missing: set[str] = field(default_factory=set)  # locked players no longer on the market

    @property
    def label(self) -> str:
        return "locked squad" if self.ids == self.locked_ids and self.locked_ids else "pending squad"


def _ids(roster: dict) -> set[str]:
    return {str(p["id"]) for p in roster.get("players", [])}


def deadline_from_config(cfg: dict) -> dt.datetime | None:
    s = (cfg.get("current_round") or {}).get("started_at")
    if not s:
        return None
    try:
        return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def trade_baseline(md_dir: Path, tmd: dict, cfg: dict, market_ids: set[str] | None = None,
                   now: dt.datetime | None = None) -> Baseline:
    """Decide the optimiser's starting squad for the matchday stored in `md_dir`."""
    pending = _ids(json.loads((md_dir / "roster.json").read_text(encoding="utf-8")))
    lf = md_dir / "roster_locked.json"
    locked = _ids(json.loads(lf.read_text(encoding="utf-8"))) if lf.exists() else set()
    max_trades = int(tmd.get("max_num_trades_per_matchday", 4))
    pending_trades = int(tmd.get("trades", 0))
    now = now or dt.datetime.now(dt.UTC)
    deadline = deadline_from_config(cfg)
    open_ = bool(deadline) and now < deadline

    if not open_:
        return Baseline(pending, 0, pending, locked, False, max_trades, pending_trades,
                        note="trade window closed - the pending squad is locked")
    if not locked:
        # no locked roster on disk (old pull, or first matchday) - best we can do is the old behaviour
        return Baseline(pending, max(max_trades - pending_trades, 0), pending, locked, True, max_trades, pending_trades,
                        note="no locked roster on disk - counting the platform's pending trades as spent")
    missing = locked - (market_ids or locked)
    if missing:
        # a locked player has left the market: the platform forces that slot to be traded anyway, so start from
        # the pending squad with whatever allowance the forced trades leave
        return Baseline(pending, max(max_trades - len(missing), 0), pending, locked, True, max_trades, pending_trades,
                        note=f"{len(missing)} locked player(s) no longer on the market - starting from the pending squad",
                        missing=missing)
    return Baseline(locked, max_trades, pending, locked, True, max_trades, pending_trades,
                    note=f"trade window open - {pending_trades} pending change(s) are reversible")


def changes_between(from_ids: set[str], to_ids: set[str]) -> tuple[set[str], set[str]]:
    """(remove, add) to turn the squad `from_ids` into `to_ids`."""
    return from_ids - to_ids, to_ids - from_ids
