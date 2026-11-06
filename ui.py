"""Design system: Limerick Christian School palette.
navy #0b3767 · gold #fdbc59 · burgundy #530100 · off-white #f8f8f8
Headings: EB Garamond · Body: Manrope
"""
from __future__ import annotations

import html

import streamlit as st

NAVY = "#0b3767"
NAVY_2 = "#184f8e"
NAVY_SOFT = "#e8eef5"
GOLD = "#fdbc59"
GOLD_DEEP = "#c98a2b"
BURGUNDY = "#530100"
BURGUNDY_2 = "#6d1717"
INK = "#14181f"
GRAY = "#7a808a"
LINE = "#e6e9ee"
GRAY_LIGHT = "#d9d9d9"
OFF_WHITE = "#f8f8f8"
SEQ = [NAVY, GOLD, BURGUNDY_2, NAVY_2, GOLD_DEEP, GRAY]

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=EB+Garamond:wght@500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"], p, li, label, input, textarea, button, select, .stMarkdown {{ font-family: 'Manrope', sans-serif !important; color: {INK}; }}
h1, h2, h3, h4, .serif {{ font-family: 'EB Garamond', serif !important; color: {NAVY}; letter-spacing: -.005em; }}
.block-container {{ padding: 0 2.2rem 3rem; max-width: 1280px; }}
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"] {{ display: none !important; }}
header[data-testid="stHeader"] {{ height: 0; background: transparent; }}
[data-testid="stSidebar"] {{ background: {OFF_WHITE}; border-right: 1px solid {LINE}; }}

/* masthead */
.mast {{ margin: 0 -2.2rem 26px; padding: 22px 2.2rem 0; background: {NAVY}; color: #fff; }}
.mast-row {{ display:flex; justify-content: space-between; align-items: flex-end; gap: 20px; flex-wrap: wrap; }}
.mast .brand {{ font-family: 'EB Garamond', serif; font-size: 2.05rem; font-weight: 600; line-height: 1; color: #fff; }}
.mast .brand span {{ color: {GOLD}; }}
.mast .sub {{ font-size: .78rem; letter-spacing: .14em; text-transform: uppercase; color: rgba(255,255,255,.62); margin-top: 8px; }}
.mast .meta {{ text-align: right; font-size: .8rem; color: rgba(255,255,255,.72); line-height: 1.55; }}
.mast .meta b {{ color: #fff; font-weight: 700; }}
.mast .rule {{ height: 4px; background: {GOLD}; margin: 18px -2.2rem 0; }}

/* tabs as a clean nav */
.stTabs [data-baseweb="tab-list"] {{ gap: 0; border-bottom: 1px solid {LINE}; }}
.stTabs [data-baseweb="tab"] {{ font-weight: 700; font-size: .92rem; color: {GRAY}; padding: 12px 18px; }}
.stTabs [aria-selected="true"] {{ color: {NAVY} !important; }}
.stTabs [data-baseweb="tab-highlight"] {{ background-color: {NAVY} !important; height: 3px; }}

/* section heads */
.eyebrow {{ font-size: .7rem; letter-spacing: .16em; text-transform: uppercase; color: {GOLD_DEEP}; font-weight: 800; }}
.h {{ font-family: 'EB Garamond', serif; font-size: 1.65rem; color: {NAVY}; font-weight: 600; margin: 2px 0 4px; line-height: 1.15; }}
.lede {{ color: {GRAY}; font-size: .9rem; margin-bottom: 14px; }}

/* stat tiles */
.stat {{ background:#fff; border:1px solid {LINE}; border-radius: 12px; padding: 16px 18px 14px; height: 100%; }}
.stat .l {{ font-size:.72rem; font-weight:800; letter-spacing:.08em; text-transform:uppercase; color:{GRAY}; }}
.stat .v {{ font-family:'EB Garamond', serif; font-size: 2.5rem; line-height: 1.05; color:{NAVY}; font-weight:600; margin-top: 6px; }}
.stat .v small {{ font-size: 1.05rem; color: {GRAY}; font-family: 'Manrope', sans-serif; font-weight: 600; margin-left: 4px; }}
.stat .s {{ font-size:.8rem; color:{GRAY}; margin-top: 4px; }}
.stat .up {{ color: #1f7a4d; font-weight: 800; }}
.stat .down {{ color: {BURGUNDY}; font-weight: 800; }}
.stat.accent {{ background:{NAVY}; border-color:{NAVY}; }}
.stat.accent .l {{ color: rgba(255,255,255,.65); }}
.stat.accent .v {{ color:#fff; }}
.stat.accent .s {{ color: rgba(255,255,255,.75); }}

/* insight strip */
.insight {{ display:flex; gap: 16px; align-items: center; background: {NAVY_SOFT}; border-radius: 12px; padding: 14px 18px; margin: 6px 0 18px; }}
.insight .n {{ font-family:'EB Garamond', serif; font-size: 2.3rem; color: {NAVY}; font-weight:700; line-height: 1; min-width: 74px; }}
.insight .t {{ font-size: .95rem; color: {INK}; }}

/* post cards */
.post {{ background:#fff; border:1px solid {LINE}; border-radius: 14px; overflow:hidden; height:100%; display:flex; flex-direction:column; }}
.post .band {{ height: 6px; }}
.post .body {{ padding: 14px 16px 16px; display:flex; flex-direction:column; gap: 8px; flex: 1; }}
.post .when {{ font-size:.72rem; font-weight:800; letter-spacing:.08em; text-transform:uppercase; color:{GOLD_DEEP}; }}
.post .ttl {{ font-family:'EB Garamond', serif; font-size: 1.35rem; color:{NAVY}; font-weight:600; line-height:1.15; }}
.post .hook {{ font-size:.9rem; color:{INK}; }}
.post .shots {{ font-size:.8rem; color:{GRAY}; }}
.tags {{ display:flex; gap:6px; flex-wrap:wrap; margin-top: auto; }}
.tag {{ font-size:.7rem; font-weight:700; padding: 3px 9px; border-radius: 999px; background:{OFF_WHITE}; color:{NAVY}; border:1px solid {LINE}; }}
.tag.dark {{ background:{NAVY}; color:#fff; border-color:{NAVY}; }}
.tag.gold {{ background:{GOLD}; color:{NAVY}; border-color:{GOLD}; }}

/* list rows */
.row-item {{ display:flex; justify-content:space-between; align-items:center; padding: 11px 0; border-bottom:1px solid {LINE}; }}
.row-item .a {{ font-weight:700; color:{NAVY}; font-size: .93rem; }}
.row-item .b {{ font-size:.78rem; color:{GRAY}; }}
.pill {{ font-size:.75rem; font-weight:800; padding: 4px 10px; border-radius: 8px; background:{OFF_WHITE}; color:{BURGUNDY}; white-space: nowrap; }}

/* chips */
.chip {{ display:inline-block; padding: 5px 12px; margin: 3px 6px 3px 0; border-radius: 999px; font-size: .82rem; font-weight:600; border:1px solid {LINE}; color:{NAVY}; background:#fff; }}

.foot {{ text-align:center; font-size:.78rem; color:{GRAY}; margin-top: 44px; padding-top: 16px; border-top:1px solid {LINE}; }}
.foot b {{ color:{NAVY}; }}
.small {{ font-size:.8rem; color:{GRAY}; }}
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button, .stLinkButton > a {{ border-radius: 10px; font-weight: 700; }}
.stFormSubmitButton > button[kind="primary"], .stButton > button[kind="primary"] {{ background:{NAVY} !important; border-color:{NAVY} !important; color:#fff !important; }}
.stButton > button[kind="primary"] p, .stFormSubmitButton > button[kind="primary"] p {{ color:#fff !important; }}
.stButton > button[kind="primary"]:hover {{ background:{NAVY_2} !important; border-color:{NAVY_2} !important; }}
[data-testid="stBaseButton-segmented_controlActive"] {{ background:{NAVY} !important; border-color:{NAVY} !important; }}
[data-testid="stBaseButton-segmented_controlActive"] p, [data-testid="stBaseButton-segmented_controlActive"] div {{ color:#fff !important; }}
</style>
"""


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def esc(x) -> str:
    return html.escape(str(x if x is not None else ""))


def head(eyebrow: str, title: str, lede: str | None = None) -> None:
    st.markdown(f'<div class="eyebrow">{esc(eyebrow)}</div><div class="h">{esc(title)}</div>'
                + (f'<div class="lede">{esc(lede)}</div>' if lede else ""), unsafe_allow_html=True)


def stat(label: str, value, sub: str = "", unit: str = "", accent: bool = False) -> str:
    return (f'<div class="stat{" accent" if accent else ""}"><div class="l">{esc(label)}</div>'
            f'<div class="v">{esc(value)}{f"<small>{esc(unit)}</small>" if unit else ""}</div><div class="s">{sub}</div></div>')


def insight(number: str, text: str) -> None:
    st.markdown(f'<div class="insight"><div class="n">{esc(number)}</div><div class="t">{text}</div></div>', unsafe_allow_html=True)


def post_card(when: str, title: str, hook: str, shots: str, tags: list[tuple[str, str]], color: str) -> str:
    t = "".join(f'<span class="tag {c}">{esc(x)}</span>' for x, c in tags)
    return (f'<div class="post"><div class="band" style="background:{color}"></div><div class="body">'
            f'<div class="when">{esc(when)}</div><div class="ttl">{esc(title)}</div>'
            f'<div class="hook">{esc(hook)}</div><div class="shots">{esc(shots)}</div><div class="tags">{t}</div></div></div>')


def chips(tags) -> str:
    return "".join(f'<span class="chip">{esc(t)}</span>' for t in tags)


def fig_style(fig, height=320, legend=True):
    fig.update_layout(
        height=height, margin=dict(l=0, r=8, t=8, b=0),
        font=dict(family="Manrope, sans-serif", color=INK, size=12),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        showlegend=legend, legend=dict(orientation="h", y=-0.18, x=0, title=None, font=dict(size=11)),
        hoverlabel=dict(font_family="Manrope, sans-serif", bgcolor="#fff"),
        bargap=0.35,
    )
    fig.update_xaxes(gridcolor=LINE, zeroline=False, linecolor=LINE, tickfont=dict(color=GRAY))
    fig.update_yaxes(gridcolor=LINE, zeroline=False, linecolor=LINE, tickfont=dict(color=INK))
    return fig


CHART_CFG = {"displayModeBar": False}
