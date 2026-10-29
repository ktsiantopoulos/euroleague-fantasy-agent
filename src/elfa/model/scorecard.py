"""Decision scorecard: how good were the matchday's decisions, not just the player projections.

For every matchday with a pre-lock snapshot (decision_mdXX_locked.json + projection_mdXX_locked.csv) and
final results, compare:
  - played team: expected (frozen projection, roles as played) vs actual platform points, z-score;
  - the agent's recommendation and the no-trade squad, both scored on actual points;
  - trade value (recommendation vs holding; your squad vs holding);
  - hindsight optimum under the same rules/budget/trade allowance -> regret;
  - captain regret (best starter's actual vs the captain's).
Writes data/processed/scorecard.csv and scorecard.md.
"""
from __future__ import annotations

import json
import math

import pandas as pd
import pulp

from elfa.config import PROCESSED, RAW

WEIGHT = {"starter": 1.0, "sixth": 1.0, "coach": 1.0, "bench": 0.5}
QUOTA = {"Guard": 4, "Forward": 4, "Center": 2, "Head Coach": 1}


def _court_role(cp: int) -> str:
    return "starter" if cp <= 5 else "sixth" if cp == 6 else "coach" if cp == 11 else "bench"


def score(squad: list[dict], pts: dict[str, float], key: str = "actual") -> float:
    """Platform scoring: starters, sixth man, coach x1; bench x0.5; captain x2."""
    tot = 0.0
    for p in squad:
        v = float(pts.get(str(p["platform_id"]), 0.0)) if key == "actual" else float(p.get(key) or 0.0)
        tot += WEIGHT[p["role"]] * v + (v if p.get("captain") else 0.0)
    return round(tot, 2)


def squad_sd(squad: list[dict], sd: dict[str, float]) -> float:
    var = 0.0
    for p in squad:
        w = WEIGHT[p["role"]] + (1.0 if p.get("captain") else 0.0)
        var += (w * float(sd.get(str(p["platform_id"]), 0.0))) ** 2
    return math.sqrt(var)


def actual_points(md: int) -> dict[str, float]:
    out = {}
    for fp in (RAW / "fantaking" / "fantasy_pts").glob(f"*_md{md:02d}.json"):
        j = json.loads(fp.read_text(encoding="utf-8"))
        if "error" in j:
            continue
        out[fp.stem.split("_md")[0]] = float(j.get("fantasy_pts") or 0.0) if j.get("match") else 0.0
    return out


def played_squad(md: int) -> tuple[list[dict], float | None]:
    """Final squad of matchday `md` (roles after in-round swaps) and the platform's team total."""
    nxt = RAW / "fantaking" / f"md_{md + 1:02d}"
    cur = RAW / "fantaking" / f"md_{md:02d}"
    for roster_fp, team_fp in ((nxt / "roster_locked.json", nxt / "team_matchday_locked.json"),
                               (cur / "roster.json", cur / "team_matchday.json")):
        if not roster_fp.exists():
            continue
        r = json.loads(roster_fp.read_text(encoding="utf-8"))
        if not r.get("players"):
            continue
        squad = [{"platform_id": str(p["id"]), "name": f"{p.get('first_name', '')} {p.get('last_name', '')}".strip(),
                  "pos": (p.get("position") or {}).get("name"), "role": _court_role(int(p["court_position"])),
                  "captain": bool(p.get("is_captain")), "pts": p.get("pts")} for p in r["players"]]
        team = None
        if team_fp.exists():
            t = json.loads(team_fp.read_text(encoding="utf-8"))
            team = t.get("pts") if "error" not in t else None
        return squad, team
    return [], None


def hindsight_best(proj: pd.DataFrame, pts: dict[str, float], budget: float, baseline: set[str], max_trades: int) -> tuple[float, list[dict]]:
    """Best squad in hindsight under the same hard rules (quota, slots, budget, trades, club cap, no centre 6th)."""
    df = proj[proj.quotation > 0].copy()
    df["platform_id"] = df.platform_id.astype(str)
    df["act"] = df.platform_id.map(pts).fillna(0.0)
    ids = list(df.platform_id)
    pos = dict(zip(ids, df.pos)); q = dict(zip(ids, df.quotation)); club = dict(zip(ids, df.team)); a = dict(zip(ids, df.act))
    players = [i for i in ids if pos[i] != "Head Coach"]
    coaches = [i for i in ids if pos[i] == "Head Coach"]
    pr = pulp.LpProblem("hindsight", pulp.LpMaximize)
    B = lambda n, ks: {k: pulp.LpVariable(f"{n}_{k}", cat="Binary") for k in ks}  # noqa: E731
    x, s, m, b, c = B("x", ids), B("s", players), B("m", players), B("b", players), B("c", players)
    pr += pulp.lpSum((s[i] + m[i] + c[i]) * a[i] + 0.5 * b[i] * a[i] for i in players) + pulp.lpSum(x[i] * a[i] for i in coaches)
    for p_, n in QUOTA.items():
        pr += pulp.lpSum(x[i] for i in ids if pos[i] == p_) == n
    for i in players:
        pr += s[i] + m[i] + b[i] == x[i]
        pr += c[i] <= s[i]
        if pos[i] == "Center":
            pr += m[i] == 0
    pr += pulp.lpSum(s.values()) == 5
    pr += pulp.lpSum(m.values()) == 1
    pr += pulp.lpSum(b.values()) == 4
    pr += pulp.lpSum(c.values()) == 1
    for p_ in ("Guard", "Forward", "Center"):
        pr += pulp.lpSum(s[i] for i in players if pos[i] == p_) >= 1
        pr += pulp.lpSum(s[i] for i in players if pos[i] == p_) <= 3
    for cl in set(club.values()):
        pr += pulp.lpSum(x[i] for i in ids if club[i] == cl) <= 6
    pr += pulp.lpSum(x[i] * q[i] for i in ids) <= budget
    if baseline:
        pr += pulp.lpSum(x[i] for i in ids if i not in baseline) <= max_trades
    pr.solve(pulp.PULP_CBC_CMD(msg=False))
    squad = []
    for i in ids:
        if (x[i].value() or 0) > 0.5:
            role = "coach" if pos[i] == "Head Coach" else "starter" if s[i].value() > 0.5 else "sixth" if m[i].value() > 0.5 else "bench"
            squad.append({"platform_id": i, "role": role, "captain": i in c and c[i].value() > 0.5, "pos": pos[i]})
    return round(pulp.value(pr.objective) or 0.0, 2), squad


def scorecard() -> tuple[pd.DataFrame, str]:
    rows = []
    for fp in sorted(PROCESSED.glob("decision_md*_locked.json")):
        md = int(fp.stem.split("md")[1].split("_")[0])
        dec = json.loads(fp.read_text(encoding="utf-8"))
        pts = actual_points(md)
        played, team_pts = played_squad(md)
        pj = PROCESSED / f"projection_md{md:02d}_locked.csv"
        if not pts or not played or not pj.exists():
            continue
        proj = pd.read_csv(pj, dtype={"platform_id": str})
        exp = dict(zip(proj.platform_id, proj.md_pts)); sd = dict(zip(proj.platform_id, proj.md_sd))
        for p in played:
            p["md_pts"] = exp.get(p["platform_id"], 0.0)
        # the roster's own per-player points are authoritative for your squad
        own = {p["platform_id"]: float(p["pts"]) for p in played if p.get("pts") is not None}
        actual = team_pts if team_pts is not None else score(played, {**pts, **own})
        expected = score(played, {}, key="md_pts")
        sdv = squad_sd(played, sd)
        rec_act, hold_act = score(dec["best"]["squad"], pts), score(dec["hold"]["squad"], pts)
        hs_pts, _hs = hindsight_best(proj, pts, float(dec["budget"]), set(dec["baseline_ids"]), int(dec["trades_left"]))
        starters = [p for p in played if p["role"] == "starter"]
        cap = next((p for p in played if p["captain"]), None)
        best_starter = max((own.get(p["platform_id"], pts.get(p["platform_id"], 0.0)) for p in starters), default=0.0)
        cap_act = own.get(cap["platform_id"], pts.get(cap["platform_id"], 0.0)) if cap else 0.0
        rows.append({
            "matchday": md, "expected": round(expected, 1), "actual": round(float(actual), 1), "sd": round(sdv, 1),
            "z": round((float(actual) - expected) / sdv, 2) if sdv else None,
            "rec_expected": round(dec["best"]["expected"], 1), "rec_actual": rec_act,
            "hold_actual": hold_act, "trade_value_rec": round(rec_act - hold_act, 1),
            "trade_value_you": round(float(actual) - hold_act, 1),
            "hindsight": hs_pts, "regret": round(hs_pts - float(actual), 1),
            "captain": cap["name"] if cap else None, "captain_regret": round(best_starter - cap_act, 1),
            "followed_rec": sorted(p["platform_id"] for p in played) == sorted(p["platform_id"] for p in dec["best"]["squad"]),
        })
    df = pd.DataFrame(rows)
    if df.empty:
        return df, "no matchday with a pre-lock decision snapshot and final results yet (first one: MD 9)"
    df.to_csv(PROCESSED / "scorecard.csv", index=False)
    lines = ["# Decision scorecard", "",
             "| MD | expected | actual | z | agent rec (actual) | no trades (actual) | trades: agent / you | hindsight | regret | captain regret |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for r in df.itertuples():
        lines.append(f"| {r.matchday} | {r.expected} ± {r.sd} | {r.actual} | {r.z:+.2f} | {r.rec_actual} | {r.hold_actual} | "
                     f"{r.trade_value_rec:+.1f} / {r.trade_value_you:+.1f} | {r.hindsight} | {r.regret} | {r.captain_regret} ({r.captain}) |")
    lines += ["", f"Mean z {df.z.mean():+.2f} (0 = unbiased; |z| > 2 on a matchday is a miss worth reading) · "
              f"mean regret {df.regret.mean():.1f} · cumulative trade value agent {df.trade_value_rec.sum():+.1f} / you {df.trade_value_you.sum():+.1f}"]
    txt = "\n".join(lines)
    (PROCESSED / "scorecard.md").write_text(txt, encoding="utf-8")
    return df, txt
