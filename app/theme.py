"""Broadcast-style theme and HTML components (from the Figma design system 'EuroLeague Fantasy — Broadcast UI').

Tokens mirror the Figma variables collection 'Broadcast'. Components are pure HTML/CSS strings rendered with
st.markdown(unsafe_allow_html=True); no JavaScript, so they work identically on desktop and phone.
"""
from __future__ import annotations

import datetime as dt
import html
import json
from zoneinfo import ZoneInfo

import altair as alt
import streamlit as st

TOKENS = {
    "base": "#0B1220", "surface": "#121C2E", "elevated": "#1A2740", "line": "#243352",
    "text": "#F3F6FB", "muted": "#8FA0BF", "dim": "#5C6B8A",
    "orange": "#FF6B1A", "gold": "#FFC43D", "pos": "#2EE59D", "neg": "#FF4D6D", "info": "#4DA3FF",
    "G": "#4DA3FF", "F": "#2EE59D", "C": "#B57BFF", "HC": "#FFC43D",
}
POS_KEY = {"Guard": "G", "Forward": "F", "Center": "C", "Head Coach": "HC"}
TEAM_NAMES: dict[str, str] = {}


def set_team_names(names: dict[str, str]) -> None:
    TEAM_NAMES.clear()
    TEAM_NAMES.update(names)


def tn(code) -> str:
    """Full club name for a code (platform or official); unknown codes pass through."""
    return TEAM_NAMES.get(str(code), str(code) if code is not None else "")

CSS = f"""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600&family=Barlow+Condensed:wght@500;600;700&display=swap" rel="stylesheet">
<style>
:root {{ {" ".join(f"--{k}: {v};" for k, v in TOKENS.items())} }}
html, body, [data-testid="stAppViewContainer"], .stApp {{ background: var(--base) !important; color: var(--text); font-family: 'Barlow', 'Helvetica Neue', Arial, sans-serif; }}
[data-testid="stSidebar"] {{ background: var(--surface) !important; border-right: 1px solid var(--line); }}
[data-testid="stHeader"] {{ background: transparent; }}
h1, h2, h3 {{ font-family: 'Barlow Condensed', 'Arial Narrow', Arial, sans-serif !important; letter-spacing: .02em; text-transform: uppercase; }}
h1 {{ font-weight: 700 !important; }}
[data-testid="stMetricValue"] {{ font-family: 'Barlow Condensed', 'Arial Narrow', Arial, sans-serif; font-weight: 700; }}
[data-testid="stMetricLabel"] {{ font-family: 'Barlow Condensed', 'Arial Narrow', Arial, sans-serif; letter-spacing: .1em; text-transform: uppercase; color: var(--muted); }}
[data-testid="stCaptionContainer"] {{ color: var(--muted); }}
div[data-testid="stDataFrame"] {{ border: 1px solid var(--line); border-radius: 12px; overflow: hidden; }}
.stButton > button[kind="primary"] {{ background: var(--orange); border: 0; color: var(--base); font-family: 'Barlow Condensed'; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }}
.block-container {{ padding-top: 1.2rem; }}

/* ---- components ---- */
.elf-hdr {{ display:flex; align-items:center; gap:14px; padding: 6px 0 14px; border-bottom: 2px solid var(--line); margin-bottom: 14px; flex-wrap: wrap; }}
.elf-mark {{ background: var(--orange); color: var(--base); font-family:'Barlow Condensed','Arial Narrow',Arial,sans-serif; font-weight:700; letter-spacing:.08em; padding: 3px 10px; border-radius: 6px; font-size: 18px; }}
.elf-title {{ font-family:'Barlow Condensed','Arial Narrow',Arial,sans-serif; font-weight:700; font-size: 22px; letter-spacing:.08em; text-transform: uppercase; }}
.elf-sub {{ color: var(--muted); font-family:'Barlow Condensed','Arial Narrow',Arial,sans-serif; font-size: 13px; letter-spacing:.08em; text-transform: uppercase; }}
.elf-grow {{ flex: 1 }}
.elf-deadline {{ text-align:right }}
.elf-deadline .big {{ font-family:'Barlow Condensed','Arial Narrow',Arial,sans-serif; font-weight:700; font-size: 24px; color: var(--orange); line-height: 1.05; }}
.elf-h1 {{ font-family:'Barlow Condensed','Arial Narrow',Arial,sans-serif; font-weight:700; font-size: 40px; letter-spacing:.02em; text-transform: uppercase; line-height: 1; margin: 6px 0 2px; }}
.elf-label {{ font-family:'Barlow Condensed','Arial Narrow',Arial,sans-serif; font-weight:500; font-size: 11px; letter-spacing:.12em; text-transform: uppercase; color: var(--muted); }}
.elf-label.orange {{ color: var(--orange); }}
.elf-grid {{ display:grid; gap: 12px; }}
.elf-card {{ background: var(--surface); border: 1px solid var(--line); border-radius: 12px; padding: 14px 16px; min-width: 0; }}
.elf-card.elev {{ background: var(--elevated); }}
.elf-kpi .v {{ font-family:'Barlow Condensed','Arial Narrow',Arial,sans-serif; font-weight:700; font-size: 36px; line-height: 1.05; margin-top: 4px; }}
.elf-kpi .s {{ color: var(--dim); font-size: 13px; margin-top: 2px; }}
.elf-chip {{ display:inline-block; font-family:'Barlow Condensed','Arial Narrow',Arial,sans-serif; font-weight:600; font-size: 11px; letter-spacing:.06em; padding: 1px 7px; border-radius: 999px; vertical-align: middle; }}
.elf-tag {{ display:inline-block; font-family:'Barlow Condensed','Arial Narrow',Arial,sans-serif; font-size: 11px; color: var(--muted); border: 1px solid var(--dim); border-radius: 4px; padding: 0 5px; margin-left: 3px; }}
.elf-trades {{ display:flex; align-items:center; gap: 10px; flex-wrap: wrap; margin-top: 8px; }}
.elf-tg {{ display:inline-flex; align-items:center; gap: 8px; background: var(--surface); border: 1px solid var(--line); border-radius: 8px; padding: 6px 12px; font-weight: 600; font-size: 14px; }}
.elf-tg .pr {{ color: var(--muted); font-family:'Barlow Condensed','Arial Narrow',Arial,sans-serif; font-weight: 600; }}
.elf-tg.out {{ border-color: var(--neg); }}  .elf-tg.in {{ border-color: var(--pos); }}
.elf-arrow {{ color: var(--orange); font-family:'Barlow Condensed','Arial Narrow',Arial,sans-serif; font-weight:700; font-size: 22px; }}
.elf-pc {{ background: var(--surface); border: 1px solid var(--line); border-radius: 12px; padding: 12px 14px; min-width: 0; }}
.elf-pc.cap {{ border: 2px solid var(--gold); }}  .elf-pc.bench {{ opacity: .62; }}
.elf-pc .top {{ display:flex; align-items:center; gap: 8px; }}
.elf-pc .nm {{ font-weight: 600; font-size: 15px; flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.elf-pc .tm {{ color: var(--muted); font-family:'Barlow Condensed','Arial Narrow',Arial,sans-serif; font-size: 12px; letter-spacing:.06em; }}
.elf-pc .num {{ display:flex; align-items: baseline; gap: 10px; margin-top: 6px; }}
.elf-pc .exp {{ font-family:'Barlow Condensed','Arial Narrow',Arial,sans-serif; font-weight:700; font-size: 32px; line-height: 1; }}
.elf-pc.cap .exp {{ color: var(--gold); }}
.elf-pc .sm {{ color: var(--muted); font-family:'Barlow Condensed','Arial Narrow',Arial,sans-serif; font-size: 12px; letter-spacing:.02em; line-height: 1.2; }}
.elf-pc .why {{ color: var(--dim); font-size: 12px; margin-top: 8px; display:flex; justify-content: space-between; gap: 8px; align-items:flex-start; }}
.elf-pc .why span:first-child {{ flex: 1; }}
.elf-row {{ display:flex; align-items:center; gap: 10px; padding: 6px 0; border-bottom: 1px solid var(--line); font-size: 14px; }}
.elf-row:last-child {{ border-bottom: 0; }}
.elf-row .val {{ font-family:'Barlow Condensed','Arial Narrow',Arial,sans-serif; font-weight:700; font-size: 18px; color: var(--pos); }}
.elf-row .val.neg {{ color: var(--neg); }}
.elf-row .mut {{ color: var(--muted); font-size: 12px; }}
.elf-note {{ display:flex; gap: 10px; align-items:flex-start; margin: 6px 0; font-size: 14px; }}
.elf-foot {{ color: var(--dim); font-size: 12px; margin-top: 10px; }}
@media (max-width: 640px) {{
  .elf-h1 {{ font-size: 32px; }}
  .elf-kpi .v {{ font-size: 30px; }}
  .elf-pc .exp {{ font-size: 28px; }}
}}
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def altair_theme():
    def _theme():
        return {"config": {
            "background": "transparent", "view": {"stroke": None},
            "font": "Barlow", "title": {"font": "Barlow Condensed", "color": TOKENS["text"]},
            "axis": {"gridColor": TOKENS["line"], "domainColor": TOKENS["line"], "tickColor": TOKENS["line"], "labelColor": TOKENS["muted"], "titleColor": TOKENS["muted"]},
            "legend": {"labelColor": TOKENS["muted"], "titleColor": TOKENS["muted"]},
            "range": {"category": [TOKENS["G"], TOKENS["F"], TOKENS["C"], TOKENS["HC"], TOKENS["orange"], TOKENS["neg"]]},
        }}
    try:  # altair >= 5.5
        alt.theme.register("elf", enable=True)(_theme)
    except Exception:  # noqa: BLE001 - older altair
        alt.themes.register("elf", _theme)
        alt.themes.enable("elf")


# ----------------------------------------------------------------------------- helpers
def _e(s) -> str:
    return html.escape("" if s is None else str(s))


def _hex_a(k: str, a: float) -> str:
    h = TOKENS[k].lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{a})"


def chip(txt: str, k: str, solid: bool = False) -> str:
    bg = TOKENS[k] if solid else _hex_a(k, 0.18)
    fg = TOKENS["base"] if solid else TOKENS[k]
    return f'<span class="elf-chip" style="background:{bg};color:{fg}">{_e(txt)}</span>'


def pos_chip(pos: str) -> str:
    k = POS_KEY.get(pos, "G")
    return chip(k, k)


def countdown(deadline_iso: str | None) -> tuple[str, str]:
    if not deadline_iso:
        return "—", ""
    d = dt.datetime.fromisoformat(deadline_iso)
    if d.tzinfo is None:
        d = d.replace(tzinfo=dt.UTC)
    now = dt.datetime.now(dt.UTC)
    secs = int((d - now).total_seconds())
    local = d.astimezone(ZoneInfo("Europe/Athens")).strftime("%a %d %b %H:%M")
    if secs <= 0:
        return "CLOSED", local
    days, rem = divmod(secs, 86400)
    hrs, rem = divmod(rem, 3600)
    mins = rem // 60
    return (f"{days}d {hrs}h {mins}m" if days else f"{hrs}h {mins}m"), local


# ----------------------------------------------------------------------------- components
def header(title: str, subtitle: str, deadline_iso: str | None, mark: str = "ELF") -> str:
    cd, local = countdown(deadline_iso)
    return (f'<div class="elf-hdr"><span class="elf-mark">{_e(mark)}</span><span class="elf-title">{_e(title)}</span>'
            f'<span class="elf-sub">{_e(subtitle)}</span><span class="elf-grow"></span>'
            f'<div class="elf-deadline"><div class="elf-label">Deadline · {_e(local)} Athens</div><div class="big">{_e(cd)}</div></div></div>')


def kpis(items: list[tuple[str, str, str, str]]) -> str:
    """items: (label, value, sub, colour-key)."""
    cards = "".join(f'<div class="elf-card elf-kpi"><div class="elf-label">{_e(l)}</div><div class="v" style="color:{TOKENS[k]}">{_e(v)}</div>'
                    + (f'<div class="s" style="color:{TOKENS["pos"] if str(s).startswith("▲") else TOKENS["dim"]}">{_e(s)}</div>' if s else "") + "</div>"
                    for l, v, s, k in items)
    return f'<div class="elf-grid" style="grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));">{cards}</div>'


def trades(out: list[dict], inn: list[dict], footer: str, title: str = "Recommended trades",
           labels: tuple[str, str] = ("OUT", "IN"), empty: str = "No trades — hold the squad") -> str:
    def tg(p, cls):
        pr = f'<span class="pr">{p["price"]:.1f}</span>' if "price" in p else ""
        return f'<span class="elf-tg {cls}">{pos_chip(p.get("pos", ""))}{_e(p["name"])}{pr}</span>'
    body = (f'<span class="elf-label" style="color:{TOKENS["neg"]}">{_e(labels[0])}</span>' + "".join(tg(p, "out") for p in out)
            + '<span class="elf-arrow">→</span>' + f'<span class="elf-label" style="color:{TOKENS["pos"]}">{_e(labels[1])}</span>' + "".join(tg(p, "in") for p in inn)) if out or inn else f"<span class='elf-sub'>{_e(empty)}</span>"
    return f'<div class="elf-card elev"><div class="elf-label orange">{_e(title)}</div><div class="elf-trades">{body}</div><div class="elf-foot">{_e(footer)}</div></div>'


def player_card(p: dict, bench: bool = False, small: bool = False) -> str:
    games = json.loads(p["games_json"]) if isinstance(p.get("games_json"), str) else []
    tags = "".join(f'<span class="elf-tag">T{g["turn"]}</span>' for g in games)
    cap = bool(p.get("captain"))
    name = _e(p["name"]) + (" <span style='color:var(--gold)'>Ⓒ ×2</span>" if cap else "")
    exp = f'{p["md_pts"]:.1f}' + (" ½" if bench else "")
    why_full = str(p.get("why", "") or "")
    why = _e(why_full if len(why_full) <= 120 else why_full[:117] + "…")
    flags = p.get("flags") or ""
    if flags and flags != "coach":
        why += f' <span style="color:{TOKENS["gold"]}">⚠ {_e(flags)}</span>'
    cls = "elf-pc" + (" cap" if cap else "") + (" bench" if bench else "")
    return (f'<div class="{cls}"><div class="top">{pos_chip(p["pos"])}<span class="nm">{name}</span><span class="tm">{_e(tn(p["team"]))}</span></div>'
            f'<div class="num"><span class="exp">{exp}</span><span class="sm">p90 {p["md_p90"]:.0f}<br>{p["quotation"]:.1f} cr</span></div>'
            f'<div class="why" title="{_e(why_full)}"><span>{why}</span><span>{tags}</span></div></div>')


def lineup_board(squad: list[dict], title: str = "Recommended squad", badges: list[str] | None = None) -> str:
    by = {r: [p for p in squad if p["role"] == r] for r in ("starter", "sixth", "bench", "coach")}
    grid = lambda cards, minw: f'<div class="elf-grid" style="grid-template-columns: repeat(auto-fit, minmax({minw}px, 1fr));">{"".join(cards)}</div>'
    parts = [('<div class="elf-card"><div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:10px">'
              f'<span class="elf-title" style="font-size:20px">{_e(title)}</span>{"".join(badges or [])}</div>')]
    parts.append('<div class="elf-label" style="margin:6px 0">Starters · 100% · captain ×2</div>' + grid([player_card(p) for p in by["starter"]], 170))
    parts.append('<div class="elf-label" style="margin:12px 0 6px">Sixth man · 100% &nbsp;·&nbsp; Coach · margin buckets</div>'
                 + grid([player_card(p) for p in by["sixth"]] + [player_card(p) for p in by["coach"]], 170))
    parts.append('<div class="elf-label" style="margin:12px 0 6px">Bench · 50% · promotable after night 1</div>' + grid([player_card(p, bench=True) for p in by["bench"]], 170))
    parts.append("</div>")
    return "".join(parts)


def notes(title: str, items: list[tuple[str, str]], chip_key: str = "info") -> str:
    body = "".join(f'<div class="elf-note">{chip(a, chip_key)}<span>{_e(b)}</span></div>' for a, b in items) or "<div class='elf-sub'>none</div>"
    return f'<div class="elf-card"><div class="elf-label orange">{_e(title)}</div>{body}</div>'


def target_rows(title: str, rows: list[dict]) -> str:
    """rows: position, team, opponent, home, DvP, best options."""
    body = ""
    for r in rows:
        v = float(r["DvP"])
        body += (f'<div class="elf-row">{pos_chip(r["position"])}<span style="font-weight:600">{_e(tn(r["team"]))} {"vs" if r["home"] == "home" else "@"} {_e(tn(r["opponent"]))}</span>'
                 f'<span class="elf-tag">{_e(r["night"])}</span><span class="elf-grow"></span><span class="val{" neg" if v < 0 else ""}">{v:+.1f}</span><span class="mut">{_e(" · ".join(x.split(" (")[0] for x in str(r["best options"]).split(", ")[:2]))}</span></div>')
    return f'<div class="elf-card"><div class="elf-label orange">{_e(title)}</div>{body or "<div class=elf-sub>none</div>"}</div>'


def md(h: str):
    st.markdown(h, unsafe_allow_html=True)
