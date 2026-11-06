"""Design system — palette from limerickchristianschool.com
navy #0b3767 · gold #fdbc59 · burgundy #530100 · off-white #f8f8f8
Headings: EB Garamond · Body: Manrope
"""
from __future__ import annotations

import html

import streamlit as st

NAVY = "#0b3767"
NAVY_2 = "#184f8e"
GOLD = "#fdbc59"
GOLD_2 = "#ffd488"
BURGUNDY = "#530100"
BURGUNDY_2 = "#6d1717"
INK = "#0f0f0f"
GRAY = "#707070"
GRAY_LIGHT = "#d9d9d9"
OFF_WHITE = "#f8f8f8"
SEQ = [NAVY, GOLD, BURGUNDY_2, NAVY_2, "#c98a2b", GRAY]

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=EB+Garamond:wght@500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"], .stMarkdown, .stText, p, li, label, input, textarea, button, select {{
  font-family: 'Manrope', sans-serif !important;
}}
h1, h2, h3, h4, h5, .serif {{ font-family: 'EB Garamond', serif !important; color: {NAVY}; letter-spacing: -.01em; }}
.block-container {{ padding-top: 1.2rem; padding-bottom: 3rem; max-width: 1320px; }}
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"] {{ visibility: hidden; height: 0; }}
header[data-testid="stHeader"] {{ background: transparent; }}

/* sidebar */
section[data-testid="stSidebar"] {{ background: {OFF_WHITE}; border-right: 1px solid rgba(11,55,103,.10); }}
section[data-testid="stSidebar"] .sb-brand {{ font-family: 'EB Garamond', serif; font-size: 1.45rem; color: {NAVY}; font-weight: 700; line-height: 1.1; }}
section[data-testid="stSidebar"] .sb-sub {{ color: {GRAY}; font-size: .8rem; text-transform: uppercase; letter-spacing: .12em; margin-bottom: .6rem; }}

/* hero */
.hero {{ background: linear-gradient(135deg, {NAVY} 0%, {NAVY_2} 100%); border-radius: 18px; padding: 26px 30px 22px;
        color: #fff; position: relative; overflow: hidden; margin-bottom: 18px; }}
.hero:after {{ content: ""; position: absolute; right: -60px; top: -60px; width: 220px; height: 220px; border-radius: 50%;
              background: radial-gradient(circle, rgba(253,188,89,.35), rgba(253,188,89,0) 70%); }}
.hero .eyebrow {{ color: {GOLD}; text-transform: uppercase; letter-spacing: .18em; font-size: .75rem; font-weight: 700; }}
.hero h1 {{ color: #fff !important; font-size: 2.35rem; margin: .15rem 0 .25rem; font-weight: 600; }}
.hero p {{ color: rgba(255,255,255,.82); margin: 0; font-size: .98rem; }}
.pills {{ margin-top: 14px; }}
.pill {{ display: inline-block; padding: 5px 12px; border-radius: 999px; font-size: .78rem; font-weight: 600; margin: 0 6px 6px 0;
        background: rgba(255,255,255,.10); border: 1px solid rgba(255,255,255,.18); color: #fff; }}
.pill.gold {{ background: {GOLD}; color: {NAVY}; border-color: {GOLD}; }}

/* KPI tiles */
.kpi {{ background: #fff; border: 1px solid rgba(11,55,103,.12); border-radius: 14px; padding: 14px 16px 12px;
       border-left: 4px solid {GOLD}; height: 100%; }}
.kpi .l {{ color: {GRAY}; font-size: .72rem; text-transform: uppercase; letter-spacing: .1em; font-weight: 700; }}
.kpi .v {{ font-family: 'EB Garamond', serif; color: {NAVY}; font-size: 1.38rem; font-weight: 600; line-height: 1.2; margin-top: 4px;
          display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; min-height: 1.2em; }}
.kpi .s {{ color: {INK}; font-size: .82rem; opacity: .75; margin-top: 2px; }}

/* section title */
.sec {{ margin: 8px 0 10px; }}
.sec h3 {{ margin: 0; font-size: 1.55rem; }}
.sec .bar {{ width: 42px; height: 3px; background: {GOLD}; border-radius: 3px; margin-top: 6px; }}
.sec .d {{ color: {GRAY}; font-size: .88rem; margin-top: 6px; }}

/* cards */
.card {{ background: #fff; border: 1px solid rgba(11,55,103,.12); border-radius: 14px; padding: 16px 18px; margin-bottom: 12px; }}
.card.soft {{ background: {OFF_WHITE}; }}
.card.navy {{ background: {NAVY}; color: #fff; border: none; }}
.card.navy h4, .card.navy b {{ color: #fff !important; }}
.card h4 {{ margin: 0 0 6px; font-size: 1.2rem; }}
.card .m {{ color: {GRAY}; font-size: .84rem; }}
.card .row {{ margin-top: 6px; font-size: .92rem; }}
.rank {{ display:inline-block; min-width: 34px; height: 34px; line-height: 34px; text-align:center; border-radius: 10px;
        background: {NAVY}; color: {GOLD}; font-weight: 800; margin-right: 10px; font-size: .9rem; }}

/* chips & badges */
.chip {{ display:inline-block; padding: 4px 11px; margin: 3px 5px 3px 0; border-radius: 999px; font-size: .82rem; font-weight: 600;
        border: 1px solid rgba(11,55,103,.22); color: {NAVY}; background: #fff; }}
.chip.hot {{ background: {NAVY}; color: #fff; border-color: {NAVY}; }}
.chip.new {{ background: {GOLD}; color: {NAVY}; border-color: {GOLD}; }}
.badge {{ display:inline-block; padding: 2px 9px; border-radius: 6px; font-size: .72rem; font-weight: 700; margin-left: 6px;
         text-transform: uppercase; letter-spacing: .04em; vertical-align: middle; }}
.b-rising {{ background: rgba(11,55,103,.09); color: {NAVY}; }}
.b-returning, .b-peak {{ background: rgba(253,188,89,.30); color: #7a4b00; }}
.b-ie {{ background: rgba(83,1,0,.08); color: {BURGUNDY}; }}
.b-use {{ background: {NAVY}; color: #fff; }}
.b-ride {{ background: {GOLD}; color: {NAVY}; }}
.b-sat {{ background: rgba(83,1,0,.12); color: {BURGUNDY}; }}
.b-watch {{ background: {OFF_WHITE}; color: {GRAY}; border: 1px solid {GRAY_LIGHT}; }}

/* tabs */
.stTabs [data-baseweb="tab-list"] {{ gap: 4px; border-bottom: 1px solid rgba(11,55,103,.12); }}
.stTabs [data-baseweb="tab"] {{ font-weight: 700; color: {GRAY}; padding: 10px 14px; }}
.stTabs [aria-selected="true"] {{ color: {NAVY} !important; }}
.stTabs [data-baseweb="tab-highlight"] {{ background-color: {GOLD} !important; height: 3px; }}

/* buttons */
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {{ border-radius: 10px; font-weight: 700; }}
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {{ background: {NAVY}; border-color: {NAVY}; }}
.stButton > button[kind="primary"]:hover, .stFormSubmitButton > button[kind="primary"]:hover {{ background: {NAVY_2}; border-color: {NAVY_2}; }}

/* score ring */
.score {{ width: 108px; height: 108px; border-radius: 50%; display:flex; align-items:center; justify-content:center;
         font-family: 'EB Garamond', serif; font-size: 2.2rem; font-weight: 700; color: {NAVY}; margin: 4px auto 8px; }}
.check {{ font-size: .9rem; margin: 3px 0; }}
.date-row {{ display:flex; justify-content: space-between; align-items:center; padding: 9px 0; border-bottom: 1px dashed rgba(11,55,103,.15); }}
.date-row .n {{ font-weight: 700; color: {NAVY}; }}
.date-row .c {{ background: {OFF_WHITE}; border-radius: 8px; padding: 3px 9px; font-weight: 800; color: {BURGUNDY}; font-size: .82rem; }}
.small {{ font-size: .8rem; color: {GRAY}; }}
</style>
"""


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def esc(x) -> str:
    return html.escape(str(x if x is not None else ""))


def section(title: str, desc: str | None = None) -> None:
    st.markdown(
        f'<div class="sec"><h3>{esc(title)}</h3><div class="bar"></div>'
        + (f'<div class="d">{esc(desc)}</div>' if desc else "") + "</div>",
        unsafe_allow_html=True,
    )


def kpi(label: str, value, sub: str = "") -> str:
    return (f'<div class="kpi"><div class="l">{esc(label)}</div><div class="v" title="{esc(value)}">{esc(value)}</div>'
            f'<div class="s">{esc(sub)}</div></div>')


def chips(tags, hot=None, new=None) -> str:
    hot, new = set(hot or []), set(new or [])
    return "".join(
        f'<span class="chip{" hot" if t in hot else " new" if t in new else ""}">{esc(t)}</span>' for t in tags
    )


def badge(text: str | None, cls: str | None = None) -> str:
    if not text:
        return ""
    if cls is None:
        t = text.lower()
        cls = "b-rising" if "ris" in t else "b-returning" if ("return" in t or "peak" in t) else "b-watch"
    return f'<span class="badge {cls}">{esc(text)}</span>'


def plotly_layout(fig, height=380):
    fig.update_layout(
        height=height, margin=dict(l=0, r=10, t=10, b=0),
        font=dict(family="Manrope, sans-serif", color=INK, size=12),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=1.08, x=0, title=None),
        hoverlabel=dict(font_family="Manrope, sans-serif"),
    )
    fig.update_xaxes(gridcolor="rgba(11,55,103,.08)", zeroline=False)
    fig.update_yaxes(gridcolor="rgba(11,55,103,.08)", zeroline=False)
    return fig
