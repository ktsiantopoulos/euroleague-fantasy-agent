"""EuroLeague Fantasy Scout — league-wide reports only (no team-specific data).

Pages: Projections, Defence vs position, Player, Top 100 managers, Market & prices, Model health.
Safe to share: it never loads roster.json / team_matchday.json and strips team details from status lines.
"""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

_ROOT = Path(__file__).resolve().parents[1]
for _p in (str(_ROOT), str(_ROOT / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from app.pages_lib import render

st.set_page_config(page_title="EuroLeague Fantasy Scout", page_icon="🔭", layout="wide")
render("scout")
