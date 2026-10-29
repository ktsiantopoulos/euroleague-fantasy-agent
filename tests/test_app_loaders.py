"""App loaders must ignore the frozen *_locked snapshots (they broke load_projection on 29 Oct)."""
import pandas as pd

from app import data as D


def test_load_projection_ignores_locked_snapshots(tmp_path, monkeypatch):
    row = {"platform_id": "1", "name": "A", "pos": "Guard", "games_json": "[]"}
    pd.DataFrame([row]).to_csv(tmp_path / "projection_md09.csv", index=False)
    pd.DataFrame([row]).to_csv(tmp_path / "projection_md09_locked.csv", index=False)
    monkeypatch.setattr(D, "PROCESSED", tmp_path)
    monkeypatch.setattr(D, "latest_matchday", lambda: 9)
    monkeypatch.setattr(D, "enrich_projection", lambda df: df)
    md, df = D.load_projection()
    assert md == 9 and len(df) == 1
