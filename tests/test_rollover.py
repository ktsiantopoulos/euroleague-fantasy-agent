"""Platform lagging on matchday rollover: switch to the next matchday only when the current round is fully played."""
import datetime as dt

from elfa.ingest.fantaking import resolve_rollover

CFG = {
    "current_matchday": {"id": 1535, "number": 8, "num_rounds": 2},
    "previous_matchday": {"id": 1534, "number": 7},
    "current_round": {"started_at": "2026-10-28T17:29:00.000000Z"},
    "matchdays": [{"id": 1535, "number": 8}, {"id": 1536, "number": 9}],
}


def _g(rnd, date, played):
    return {"round": rnd, "utcDate": date, "played": played, "phaseType": {"code": "RS"}}


SCHED_R8_DONE = [_g(8, "2026-10-27T16:00:00Z", True), _g(8, "2026-10-28T17:30:00Z", True),
                 _g(9, "2026-10-29T19:00:00Z", False), _g(9, "2026-10-30T16:00:00Z", False)]
MORNING = dt.datetime(2026, 10, 29, 4, 13, tzinfo=dt.UTC)


def test_rolls_over_when_current_round_is_fully_played():
    eff, note = resolve_rollover(CFG, SCHED_R8_DONE, now=MORNING)
    assert note and eff["current_matchday"] == {"id": 1536, "number": 9, "num_rounds": 2}
    assert eff["previous_matchday"] == {"id": 1535, "number": 8}
    assert eff["current_round"]["started_at"] == "2026-10-29T18:59:00.000000Z"
    assert CFG["current_matchday"]["number"] == 8  # input untouched


def test_no_rollover_mid_matchday():
    sched = [_g(8, "2026-10-27T16:00:00Z", True), _g(8, "2026-10-28T17:30:00Z", False)] + SCHED_R8_DONE[2:]
    eff, note = resolve_rollover(CFG, sched, now=dt.datetime(2026, 10, 28, 12, tzinfo=dt.UTC))
    assert note is None and eff is CFG


def test_no_rollover_once_next_round_has_tipped_off():
    eff, note = resolve_rollover(CFG, SCHED_R8_DONE, now=dt.datetime(2026, 10, 29, 19, 30, tzinfo=dt.UTC))
    assert note is None and eff is CFG


def test_no_rollover_without_schedule():
    eff, note = resolve_rollover(CFG, [], now=MORNING)
    assert note is None and eff is CFG
