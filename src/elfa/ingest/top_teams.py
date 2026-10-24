"""Crawl the Global league standings and the public roster preview of the top-N teams.

Endpoints (read-only, bearer token):
  /api/v1/tournaments/{tid}/standings?page=N          -> fantasy team ids, names, total pts
  /api/v1/fantasy-teams/{id}/matchdays/{md}/roster/preview  -> public lineup for a played matchday
Raw JSON is cached under data/raw/top/<tournament>/md_<n>/<team>.json; already-fetched files are skipped.
"""
from __future__ import annotations

import json
from pathlib import Path

from elfa.config import RAW
from elfa.ingest.fantaking import FantakingClient

GLOBAL_TOURNAMENT = 191896


def top_dir(tid: int) -> Path:
    d = RAW / "top" / str(tid)
    d.mkdir(parents=True, exist_ok=True)
    return d


def standings(client: FantakingClient, tid: int = GLOBAL_TOURNAMENT, n: int = 100) -> list[dict]:
    out: list[dict] = []
    page = 1
    while len(out) < n:
        j = client.get(f"/api/v1/tournaments/{tid}/standings", page=page, per_page=100)
        data = j.get("data", [])
        out.extend(data)
        meta = j.get("meta") or {}
        last = meta.get("last_page")
        if not data or (last is not None and page >= int(last)) or (last is None and len(data) < 25):
            break
        page += 1
    out = out[:n]
    (top_dir(tid) / "standings.json").write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    return out


def pull_top(client: FantakingClient, matchdays: list[dict], tid: int = GLOBAL_TOURNAMENT, n: int = 100) -> int:
    """Fetch roster previews for the top-n teams for every matchday in `matchdays` (id, number)."""
    teams = standings(client, tid, n)
    fetched = 0
    for m in matchdays:
        d = top_dir(tid) / f"md_{m['number']:02d}"
        d.mkdir(exist_ok=True)
        for t in teams:
            fp = d / f"{t['id']}.json"
            if fp.exists():
                continue
            try:
                j = client.get(f"/api/v1/fantasy-teams/{t['id']}/matchdays/{m['id']}/roster/preview")
            except Exception as e:  # noqa: BLE001
                fp.write_text(json.dumps({"error": type(e).__name__}), encoding="utf-8")
                continue
            fp.write_text(json.dumps(j.get("data", j), ensure_ascii=False), encoding="utf-8")
            fetched += 1
    return fetched
