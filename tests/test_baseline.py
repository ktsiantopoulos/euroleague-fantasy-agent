"""Trade baseline: locked squad + full allowance while the window is open, pending squad + nothing after it."""
import datetime as dt
import json

from elfa.model.baseline import changes_between, trade_baseline


def _write(tmp_path, pending, locked=None):
    (tmp_path / "roster.json").write_text(json.dumps({"players": [{"id": i} for i in pending]}))
    if locked is not None:
        (tmp_path / "roster_locked.json").write_text(json.dumps({"players": [{"id": i} for i in locked]}))


CFG = {"current_round": {"started_at": "2026-10-27T15:59:00.000000Z"}}
TMD = {"max_num_trades_per_matchday": 4, "trades": 4}
BEFORE = dt.datetime(2026, 10, 26, 12, tzinfo=dt.UTC)
AFTER = dt.datetime(2026, 10, 27, 18, tzinfo=dt.UTC)


def test_window_open_starts_from_locked_with_full_allowance(tmp_path):
    _write(tmp_path, pending=[1, 2, 3, 20, 21, 22, 23], locked=[1, 2, 3, 10, 11, 12, 13])
    b = trade_baseline(tmp_path, TMD, CFG, market_ids={str(i) for i in range(1, 30)}, now=BEFORE)
    assert b.open and b.label == "locked squad"
    assert b.ids == {"1", "2", "3", "10", "11", "12", "13"} and b.trades_left == 4
    assert b.pending_ids == {"1", "2", "3", "20", "21", "22", "23"} and b.pending_trades == 4


def test_window_closed_locks_the_pending_squad(tmp_path):
    _write(tmp_path, pending=[1, 2, 3, 20], locked=[1, 2, 3, 10])
    b = trade_baseline(tmp_path, TMD, CFG, now=AFTER)
    assert not b.open and b.ids == {"1", "2", "3", "20"} and b.trades_left == 0


def test_no_locked_roster_falls_back_to_old_counting(tmp_path):
    _write(tmp_path, pending=[1, 2, 3, 20])
    b = trade_baseline(tmp_path, {"max_num_trades_per_matchday": 4, "trades": 1}, CFG, now=BEFORE)
    assert b.open and b.ids == {"1", "2", "3", "20"} and b.trades_left == 3 and b.label == "pending squad"


def test_locked_player_gone_from_market_forces_pending_baseline(tmp_path):
    _write(tmp_path, pending=[1, 2, 3, 20], locked=[1, 2, 3, 99])
    b = trade_baseline(tmp_path, TMD, CFG, market_ids={"1", "2", "3", "20"}, now=BEFORE)
    assert b.ids == {"1", "2", "3", "20"} and b.trades_left == 3 and b.missing == {"99"}


def test_changes_between():
    assert changes_between({"a", "b", "c"}, {"a", "c", "d"}) == ({"b"}, {"d"})
