"""EuroLeague Fantasy Agent — private dashboard (all reports + my team).

Reads the files the GitHub Actions pipeline commits; the what-if page runs the real optimiser.
Deploy this file as the private app; app/scout_app.py is the league-wide scouting app.
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

st.set_page_config(page_title="EuroLeague Fantasy Agent", page_icon="🏀", layout="wide")
render("team")
