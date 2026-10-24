"""What the top managers actually do: ownership, captains, trades, in-round swaps, budget use.

Input: data/raw/top/<tid>/md_XX/<team>.json (roster previews) + standings.json.
Outputs (data/processed): top_rosters.csv (one row per team x matchday x player), top_insights.md.
"""
from __future__ import annotations

import json
from itertools import pairwise

import pandas as pd

from elfa.config import PROCESSED, RAW
from elfa.ingest.top_teams import GLOBAL_TOURNAMENT

SLOT = {1: "S", 2: "S", 3: "S", 4: "S", 5: "S", 6: "6th", 7: "B", 8: "B", 9: "B", 10: "B", 11: "HC"}


def load_top_rosters(tid: int = GLOBAL_TOURNAMENT) -> pd.DataFrame:
    base = RAW / "top" / str(tid)
    st = {t["id"]: t for t in json.loads((base / "standings.json").read_text(encoding="utf-8"))} if (base / "standings.json").exists() else {}
    rows = []
    for md_dir in sorted(base.glob("md_*")):
        md = int(md_dir.name.split("_")[1])
        for fp in md_dir.glob("*.json"):
            j = json.loads(fp.read_text(encoding="utf-8"))
            if "error" in j or not j.get("players"):
                continue
            team_id = int(fp.stem)
            for p in j["players"]:
                cp = int(p.get("court_position") or 0)
                rows.append({
                    "team_id": team_id, "team_name": st.get(team_id, {}).get("name"), "rank": st.get(team_id, {}).get("position"),
                    "matchday": md, "team_pts_md": j.get("pts"), "trades": j.get("trades"), "formation_id": j.get("formation_id"),
                    "player_id": str(p["id"]), "player": f"{p.get('first_name','')} {p.get('last_name','')}".strip(),
                    "pos": (p.get("position") or {}).get("name"), "club": (p.get("team") or {}).get("abbreviation"),
                    "court_position": cp, "slot": SLOT.get(cp, "?"), "captain": bool(p.get("is_captain")),
                    "pts": p.get("pts"), "quotation": p.get("quotation"), "from_bench": bool(p.get("started_from_bench")),
                })
    df = pd.DataFrame(rows)
    if len(df):
        df.to_csv(PROCESSED / "top_rosters.csv", index=False)
    return df


def analyse(df: pd.DataFrame, market: list[dict] | None = None) -> str:
    if df.empty:
        return "no top-team rosters pulled yet"
    n_teams = df.team_id.nunique()
    mds = sorted(df.matchday.unique())
    lines = [f"# Top-{n_teams} managers — matchdays {mds[0]}–{mds[-1]}", ""]

    # 1) ownership by matchday (field vs bench), compared with global popularity if market given
    last = df[df.matchday == mds[-1]]
    own = last.groupby(["player", "pos", "club"]).agg(teams=("team_id", "nunique"), field=("slot", lambda s: (s != "B").sum()),
                                                      captain=("captain", "sum"), price=("quotation", "mean")).reset_index()
    own["own%"] = (100 * own.teams / n_teams).round(0)
    pop = {}
    if market:
        pop = {f"{m.get('first_name','')} {m.get('last_name','')}".strip(): m.get("popularity") for m in market}
        own["global%"] = own.player.map(lambda n: round(100 * (pop.get(n) or 0)))
        own["edge"] = own["own%"] - own["global%"]
    own = own.sort_values("teams", ascending=False)
    lines += [f"## Ownership in the top {n_teams}, matchday {mds[-1]}", "",
              "| player | pos | club | price | top own% | global% | captain # |", "|---|---|---|---|---|---|---|"]
    for r in own.head(20).itertuples():
        g = getattr(r, "global%", "")
        lines.append(f"| {r.player} | {r.pos[0]} | {r.club} | {r.price:.1f} | {r._8:.0f} | {g} | {int(r.captain)} |")
    if "edge" in own:
        lines += ["", "**Most over-owned by the elite vs the crowd** (where their edge is): " +
                  ", ".join(f"{r.player} (+{r.edge:.0f} pp)" for r in own.sort_values("edge", ascending=False).head(8).itertuples())]

    # 2) captains
    caps = df[df.captain].groupby("matchday").player.agg(lambda s: s.value_counts().head(3).to_dict())
    lines += ["", "## Captain choices (top 3 per matchday)"]
    for md, d in caps.items():
        lines.append(f"- MD{md}: " + ", ".join(f"{k} ({v})" for k, v in d.items()))

    # 3) trades per matchday and the most common moves
    tr = df.groupby(["matchday", "team_id"]).trades.first().groupby("matchday").mean().round(2)
    lines += ["", "## Trades used per team (mean)", "- " + ", ".join(f"MD{md}: {v}" for md, v in tr.items())]
    moves_in, moves_out = {}, {}
    for tid, g in df.groupby("team_id"):
        by_md = {md: set(x.player) for md, x in g.groupby("matchday")}
        for a, b in pairwise(mds):
            if a in by_md and b in by_md:
                for p in by_md[b] - by_md[a]:
                    moves_in[(b, p)] = moves_in.get((b, p), 0) + 1
                for p in by_md[a] - by_md[b]:
                    moves_out[(b, p)] = moves_out.get((b, p), 0) + 1
    lines += ["", "## Most common moves (count of top teams)"]
    for md in mds[1:]:
        ins = sorted(((p, c) for (m, p), c in moves_in.items() if m == md), key=lambda x: -x[1])[:4]
        outs = sorted(((p, c) for (m, p), c in moves_out.items() if m == md), key=lambda x: -x[1])[:4]
        lines.append(f"- MD{md}: IN " + ", ".join(f"{p} ({c})" for p, c in ins) + " · OUT " + ", ".join(f"{p} ({c})" for p, c in outs))

    # 4) in-round swaps
    fb = df[df.from_bench & (df.slot != "B")]
    share = df[df.slot != "B"].groupby("matchday").apply(lambda g: g.from_bench.mean()).round(3)
    lines += ["", "## In-round management", "- Field players promoted from the bench during the round: " + ", ".join(f"MD{md}: {100*v:.0f}%" for md, v in share.items()),
              f"- Average points of promoted players: {fb.pts.mean():.1f} vs {df[(df.slot != 'B') & ~df.from_bench].pts.mean():.1f} for players who started on the field"]

    # 5) budget structure
    last_nb = last[last.slot != "HC"]
    slot_price = last_nb.groupby("slot").quotation.mean().round(1)
    lines += ["", f"## Budget structure (matchday {mds[-1]}, mean price per slot)",
              "- " + ", ".join(f"{k}: {v}" for k, v in slot_price.items()),
              f"- Price of the most expensive player per team: {last_nb.groupby('team_id').quotation.max().mean():.1f} · cheapest: {last_nb.groupby('team_id').quotation.min().mean():.1f}",
              f"- Players per club (max per team): {last.groupby('team_id').club.agg(lambda s: s.value_counts().max()).mean():.1f}"]

    # 6) coaches
    hc = df[df.slot == "HC"].groupby("matchday").player.agg(lambda s: s.value_counts().head(3).to_dict())
    lines += ["", "## Coach choices (top 3 per matchday)"]
    for md, d in hc.items():
        lines.append(f"- MD{md}: " + ", ".join(f"{k} ({v})" for k, v in d.items()))

    txt = "\n".join(lines)
    (PROCESSED / "top_insights.md").write_text(txt, encoding="utf-8")
    return txt
