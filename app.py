"""LCS · IDEAs for Posting
Social media planning dashboard for Limerick Christian School (primary & secondary).
Developer: Ed Trigueros
Run: streamlit run app.py
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

import importlib

import insights as ins
import copylab
import studio
import ui

# Streamlit Cloud keeps imported modules in memory between deploys; reload so new helpers are always picked up.
for _m in (ui, ins, studio, copylab):
    importlib.reload(_m)
from ui import BURGUNDY_2, CHART_CFG, GOLD, GOLD_DEEP, GRAY_LIGHT, NAVY, OFF_WHITE, esc

APP_NAME, DEVELOPER = "LCS – IDEAs for Posting", "Ed Trigueros"
ROOT = Path(__file__).parent
TZ = ZoneInfo("Europe/Dublin")
TODAY = datetime.now(TZ).date()

st.set_page_config(page_title=APP_NAME, page_icon="📘", layout="wide", initial_sidebar_state="collapsed")
ui.inject_css()


@st.cache_data(ttl=3600)
def load(p: str) -> dict:
    return json.loads((ROOT / p).read_text(encoding="utf-8"))


EDU = load("config/edu.json")
BM = load("data/benchmark.json")
INS = load("config/insights.json")
TRENDS = load("data/latest.json")
PILLAR_COLORS = EDU["pillars"]

schools = pd.DataFrame(BM["schools"])
schools["er"] = (schools["avg_eng"] / schools["followers"] * 100).round(1)
HIST = pd.read_csv(ROOT / "data" / "ig_history.csv", parse_dates=["date"]) if (ROOT / "data" / "ig_history.csv").exists() else pd.DataFrame()
if not HIST.empty:  # latest public follower counts (auto-updated every Monday)
    latest = HIST.sort_values("date").groupby("handle").tail(1).set_index("handle")
    schools["followers"] = schools["handle"].map(latest["followers"]).fillna(schools["followers"]).astype(int)
    if "avg_eng" in latest:  # engagement refreshed automatically when the Instagram API is connected
        schools["avg_eng"] = pd.to_numeric(schools["handle"].map(latest["avg_eng"]), errors="coerce").fillna(schools["avg_eng"]).round().astype(int)
    schools["er"] = (schools["avg_eng"] / schools["followers"] * 100).round(1)
lcs = schools[schools["group"] == "LCS"].iloc[0]

# --------------------------------------------------------------------------- #
# Masthead + controls
# --------------------------------------------------------------------------- #
week_start = TODAY - timedelta(days=TODAY.weekday())
st.markdown(
    f"""<div class="mast"><div class="mast-row">
<div><div class="brand">LCS <span>·</span> IDEAs for Posting</div>
<div class="sub">Social media planning · Limerick Christian School</div></div>
<div class="meta">Week of <b>{week_start.strftime('%d %B %Y')}</b> · updated every Monday<br>Principal: <b>Naomi Rose</b><br>Developer: <b>{DEVELOPER}</b></div>
</div><div class="rule"></div></div>""",
    unsafe_allow_html=True,
)

c1, c2 = st.columns([1.2, 3])
segment = c1.segmented_control("School level", ["All", "Primary", "Secondary"], default="All", key="level") or "All"
platform = "Instagram"
c2.markdown(f'<div class="small" style="padding-top:34px">Showing <b>{"primary and secondary" if segment == "All" else segment.lower()}</b>: '
            'ideas, posts, competitors, hashtags and copy all follow this choice. This dashboard updates automatically every Monday.</div>',
            unsafe_allow_html=True)

LEVEL_MATCH = {"All": lambda lv: True, "Primary": lambda lv: "Primary" in lv, "Secondary": lambda lv: "Secondary" in lv}[segment]
schools_all = schools
schools = schools_all[schools_all["level"].apply(LEVEL_MATCH) | (schools_all["group"] == "LCS")].copy()
lim = schools[schools["group"] == "Limerick"]
lim_label = {"All": "Limerick schools", "Primary": "Limerick primary schools", "Secondary": "Limerick secondary schools"}[segment]
lim_avg = {"followers": int(lim["followers"].mean()), "er": round(lim["er"].mean(), 1), "pw": round(lim["per_week"].mean(), 1)}


def ideas_for(seg: str) -> list[dict]:
    return [i for i in EDU["ideas"] if seg == "All" or i["segment"] in (seg, "Both")]


def lvl(s: str) -> str:
    return "All levels" if s == "Both" else s


def plat_label(p: str) -> str:
    return {"Both": "Instagram + Facebook", "Instagram": "Instagram", "Facebook": "Facebook"}[p]


def next_slots(plat: str, n: int = 3) -> list[datetime]:
    now = datetime.now(TZ)
    out = []
    if plat == "Facebook":
        fb = EDU["best_times"]["facebook"]
        for k in range(0, 10):
            d = (now + timedelta(days=k)).date()
            hrs = fb.get(d.strftime("%a"))
            if hrs:
                dt = datetime(d.year, d.month, d.day, hrs[0], tzinfo=TZ)
                if dt > now:
                    out.append(dt)
    else:
        out = [s["dt"] for s in sorted(ins.next_slots(INS["posting_times"], n=6), key=lambda s: s["dt"])]
    seen, res = set(), []
    for dt in out:
        if dt.date() not in seen:
            seen.add(dt.date())
            res.append(dt)
    return res[:n]


T = st.tabs(["This week", "Growth", "How we compare", "Post ideas", "Calendar", "Trends", "Copy lab"])

# --------------------------------------------------------------------------- #
# 1 · This week
# --------------------------------------------------------------------------- #
with T[0]:
    deadline = date.fromisoformat(EDU["school"]["promo_deadline"]["date"])
    days_left = (deadline - TODAY).days
    s = st.columns(4)
    s[0].markdown(ui.stat("Instagram followers", f"{int(lcs.followers):,}",
                          f"{lim_label} average {lim_avg['followers']:,}"), unsafe_allow_html=True)
    s[1].markdown(ui.stat("Engagement rate", lcs.er, f'<span class="up">{lcs.er / lim_avg["er"]:.0f}× the local average</span> · small, loyal audience',
                          unit="%", accent=True), unsafe_allow_html=True)
    s[2].markdown(ui.stat("Posts per week", lcs.per_week, f'<span class="down">{lim_label} post {lim_avg["pw"]} a week</span>'),
                  unsafe_allow_html=True)
    s[3].markdown(ui.stat("Offer deadline", max(days_left, 0), f'{EDU["school"]["promo_deadline"]["label"]} · {deadline.strftime("%d %b")}',
                          unit="days"), unsafe_allow_html=True)

    st.write("")
    faith, enrol = lcs.pillar_eng.get("Faith & values", 0), lcs.pillar_eng.get("Enrolment", 0)
    if enrol:
        ui.insight(f"{faith / enrol:.0f}×", "On our Instagram, <b>faith and school-life posts</b> earn four times the engagement of "
                   "<b>promotional enrolment posts</b>. Parents respond to real moments first.")

    ui.head("This week", "Three posts to publish", f"{segment if segment != 'All' else 'Primary and secondary'} · {platform}")
    pool = {i["id"]: i for i in ideas_for(segment)}
    pick = []
    if days_left >= 0 and "b1" in pool:
        pick.append(pool["b1"])
    if 0 <= (date(2026, 11, 29) - TODAY).days <= 30:
        pick.append(pool.get("s4") if segment == "Secondary" else pool.get("p4"))
    for cid in (["p1", "s1"] if segment == "All" else ["p1"] if segment == "Primary" else ["s1"]):
        if cid in pool:
            pick.append(pool[cid])
    for i in pool.values():
        if len([p for p in pick if p]) >= 3:
            break
        if i not in pick and i["goal"] == "Trust":
            pick.append(i)
    pick = [p for p in pick if p][:3]
    slots = next_slots(platform, 3)
    cols = st.columns(3)
    for k, (col, idea) in enumerate(zip(cols, pick)):
        when = slots[k].strftime("%A %d %b · %H:%M") if k < len(slots) else ""
        col.markdown(ui.post_card(when, idea["title"], idea["hook"], idea["shots"],
                                  [(idea["format"], "dark"), (idea["pillar"], ""), (lvl(idea["segment"]), "")],
                                  PILLAR_COLORS.get(idea["pillar"], NAVY)), unsafe_allow_html=True)

    st.write("")
    h1, h2 = st.columns([1.5, 1])
    with h1:
        ui.head("Timing", f"Best hours on {platform}",
                "Education accounts, local time." if platform == "Facebook" else "Local time.")
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        hours = list(range(7, 22))
        if platform == "Facebook":
            fb = EDU["best_times"]["facebook"]
            z = [[(1.0 if h in fb.get(d, []) else 0.14 if d in fb else 0.03) for h in hours] for d in days]
        else:
            g = ins.heat_grid(INS["posting_times"])
            piv = g.pivot(index="day", columns="hour", values="score").reindex(days)
            z = [[piv.loc[d, h] / 100 if h in piv.columns else 0 for h in hours] for d in days]
        fig = go.Figure(go.Heatmap(z=z, x=[f"{h}:00" for h in hours], y=days, showscale=False, xgap=3, ygap=3,
                                   colorscale=[[0, OFF_WHITE], [0.5, "#b9c9dd"], [1, NAVY]], hoverinfo="skip"))
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(ui.fig_style(fig, 270, legend=False), width="stretch", config=CHART_CFG)
    with h2:
        ui.head("Next slots", "Book these in")
        for dt in slots:
            st.markdown(f'<div class="row-item"><span class="a">{dt.strftime("%A %d %B")}</span><span class="pill">{dt.strftime("%H:%M")}</span></div>',
                        unsafe_allow_html=True)
        st.write("")
        for m in [m for m in EDU["moments"] if date.fromisoformat(m["date"]) >= TODAY][:2]:
            d = date.fromisoformat(m["date"])
            st.markdown(f'<div class="row-item"><span><span class="a">{esc(m["name"])}</span><br><span class="b">{d.strftime("%d %b")}</span></span>'
                        f'<span class="pill">{(d - TODAY).days} days</span></div>', unsafe_allow_html=True)

# --------------------------------------------------------------------------- #
# 2 · Growth
# --------------------------------------------------------------------------- #
with T[1]:
    hist = HIST.copy()
    dates = sorted(hist["date"].unique()) if not hist.empty else []
    last_d = pd.Timestamp(dates[-1]).strftime("%d %b %Y") if dates else "–"
    ui.head("Growth", "Followers and momentum", f"Public Instagram numbers, updated automatically every Monday · last update {last_d}")

    # ---- goal + health -------------------------------------------------------
    g1, g2 = st.columns([1, 1.25])
    with g1:
        target = st.number_input("Follower goal for June 2027", min_value=200, max_value=20000, value=500, step=50)
        cur = int(lcs.followers)
        weeks_left = max((date(2027, 6, 30) - TODAY).days / 7, 1)
        need = max(target - cur, 0) / weeks_left
        pct = min(cur / target, 1)
        st.markdown(
            f"""<div class="stat"><div class="l">Progress to goal</div>
<div class="v">{cur:,}<small>/ {target:,}</small></div>
<div style="height:10px;background:#eef1f5;border-radius:6px;margin:10px 0 6px;overflow:hidden">
<div style="width:{pct*100:.0f}%;height:100%;background:{GOLD}"></div></div>
<div class="s">Needs <b>{need:.0f} new followers a week</b> until 30 June 2027</div></div>""", unsafe_allow_html=True)
    with g2:
        days_since = (TODAY - date.fromisoformat(lcs.last_post)).days
        parts = {
            "Posting rhythm": min(lcs.per_week / 3, 1) * 100,
            "Engagement": min(lcs.er / max(lim_avg["er"], 0.1), 1) * 100,
            "Reels share": min((lcs.reels / max(lcs["sample"], 1)) / 0.4, 1) * 100,
            "Recency": max(0, 100 - days_since * 10),
        }
        score = round(sum(parts.values()) / len(parts))
        bars = "".join(
            f'<div style="display:flex;align-items:center;gap:10px;margin:7px 0"><div style="width:120px;font-size:.82rem;color:#14181f">{k}</div>'
            f'<div style="flex:1;height:8px;background:#eef1f5;border-radius:5px;overflow:hidden"><div style="width:{v:.0f}%;height:100%;'
            f'background:{NAVY if v >= 60 else GOLD if v >= 30 else BURGUNDY_2}"></div></div><div style="width:34px;text-align:right;font-size:.8rem;font-weight:700">{v:.0f}</div></div>'
            for k, v in parts.items())
        st.markdown(f'<div class="stat"><div class="l">Account health · LCS</div><div style="display:flex;gap:22px;align-items:center">'
                    f'<div class="v" style="font-size:3.2rem">{score}<small>/100</small></div><div style="flex:1">{bars}</div></div>'
                    f'<div class="s">Targets: 3 posts a week · local engagement average · 40% Reels · a post in the last 7 days</div></div>',
                    unsafe_allow_html=True)

    st.write("")
    # ---- watchlist -------------------------------------------------------------
    ui.head("Watchlist", "Competitor tracker")
    names = dict(zip(schools["handle"], schools["short"]))
    groups = dict(zip(schools["handle"], schools["group"]))
    rows = []
    for h, gdf in (hist[hist["handle"].isin(schools["handle"])].groupby("handle") if not hist.empty else []):
        gdf = gdf.sort_values("date")
        f_now, p_now = int(gdf["followers"].iloc[-1]), gdf["posts"].iloc[-1]
        f_prev = int(gdf["followers"].iloc[-2]) if len(gdf) > 1 else None
        p_prev = gdf["posts"].iloc[-2] if len(gdf) > 1 else None
        rows.append({
            "School": names.get(h, h), "Group": {"LCS": "LCS", "Limerick": "Limerick", "Ireland reference": "Ireland"}.get(groups.get(h), ""),
            "Followers": f_now,
            "Change": (f_now - f_prev) if f_prev is not None else None,
            "Change %": round((f_now - f_prev) / f_prev * 100, 1) if f_prev else None,
            "New posts": int(p_now - p_prev) if p_prev is not None else None,
            "Engagement %": float(schools.loc[schools["handle"] == h, "er"].iloc[0]),
            "Trend": gdf["followers"].tolist(),
            "Profile": f"https://www.instagram.com/{h}/",
        })
    wl = pd.DataFrame(rows).sort_values("Followers", ascending=False) if rows else pd.DataFrame()
    _fmt = {"Change": lambda v: f"{int(v):+,d}", "Change %": lambda v: f"{v:+.1f}%", "New posts": lambda v: f"{int(v)}"}
    for _c, _f in _fmt.items():
        if _c in wl:
            wl[_c] = [("–" if v is None or pd.isna(v) else _f(v)) for v in wl[_c]]
    if not wl.empty:
        st.dataframe(
            wl, hide_index=True, width="stretch",
            column_config={
                "Followers": st.column_config.NumberColumn(format="localized"),
                "Change": st.column_config.TextColumn("Δ week"),
                "Change %": st.column_config.TextColumn("Δ %"),
                "New posts": st.column_config.TextColumn("Posts this week"),
                "Engagement %": st.column_config.ProgressColumn("Engagement rate", format="%.1f%%", min_value=0, max_value=25),
                "Trend": st.column_config.LineChartColumn("Followers trend", y_min=None, y_max=None),
                "Profile": st.column_config.LinkColumn("Profile", display_text="Open"),
            })
        if len(dates) < 2:
            st.markdown('<div class="small">First snapshot: 6 Nov 2026. Weekly change and trend lines fill in from the next Monday update.</div>',
                        unsafe_allow_html=True)

    st.write("")
    c1, c2 = st.columns([1.5, 1])
    with c1:
        ui.head("Growth curve", "Follower growth, indexed")
        if len(dates) >= 2:
            hh = hist.copy()
            hh["base"] = hh.groupby("handle")["followers"].transform("first")
            hh["index"] = hh["followers"] / hh["base"] * 100
            hh["School"] = hh["handle"].map(names)
            fig = px.line(hh, x="date", y="index", color="School", markers=True,
                          color_discrete_map={"LCS": GOLD}, labels={"index": "Growth (first week = 100)", "date": ""})
            fig.update_traces(line=dict(width=2))
            fig.for_each_trace(lambda t: t.update(line=dict(width=4)) if t.name == "LCS" else t.update(opacity=.55))
            st.plotly_chart(ui.fig_style(fig, 320), width="stretch", config=CHART_CFG)
        else:
            st.markdown('<div class="stat" style="display:flex;align-items:center;justify-content:center;min-height:240px;color:#7a808a">'
                        'The growth curve appears after the second weekly snapshot (Monday).</div>', unsafe_allow_html=True)
    with c2:
        ui.head("Share of voice", f"Followers among {lim_label.lower().replace('limerick', 'Limerick')}")
        sv = schools[schools["group"].isin(["LCS", "Limerick"])].sort_values("followers", ascending=False)
        fig = go.Figure(go.Pie(labels=sv["short"], values=sv["followers"], hole=.66, sort=False,
                               marker=dict(colors=[GOLD if g == "LCS" else c for g, c in
                                                   zip(sv["group"], [NAVY, "#184f8e", "#6d8fb8", "#9fb6d1", "#c9d6e6", "#dfe6ef", "#eef1f5"])],
                                           line=dict(color="#fff", width=2)),
                               textinfo="none", hovertemplate="%{label}: %{value:,} (%{percent})<extra></extra>"))
        share = float(sv.loc[sv["group"] == "LCS", "followers"].sum() / sv["followers"].sum() * 100)
        fig.update_layout(annotations=[dict(text=f"<b>{share:.1f}%</b><br>LCS", showarrow=False, font=dict(size=18, color=NAVY))])
        st.plotly_chart(ui.fig_style(fig, 300), width="stretch", config=CHART_CFG)

    # ---- LCS insights (Graph API) ------------------------------------------------
    st.write("")
    ui.head("Inside the account", "LCS Instagram insights")
    ins_path = ROOT / "data" / "lcs_insights.json"
    if ins_path.exists():
        LI = json.loads(ins_path.read_text())
        t = LI.get("last_28_days", {})
        k = st.columns(4)
        for col, (lab, key) in zip(k, [("Accounts reached", "reach"), ("Profile visits", "profile_views"),
                                         ("Website clicks", "website_clicks"), ("Interactions", "total_interactions")]):
            col.markdown(ui.stat(lab, f"{t.get(key, 0):,}", "last 28 days"), unsafe_allow_html=True)
        demo = LI.get("followers_by", {})
        if demo.get("city"):
            d = pd.DataFrame(demo["city"]).sort_values("v")
            fig = go.Figure(go.Bar(x=d["v"], y=d["k"], orientation="h", marker_color=NAVY))
            st.markdown("**Where followers live**")
            st.plotly_chart(ui.fig_style(fig, 260, legend=False), width="stretch", config=CHART_CFG)
        if LI.get("media"):
            st.dataframe(pd.DataFrame(LI["media"]), hide_index=True, width="stretch",
                         column_config={"permalink": st.column_config.LinkColumn("Post", display_text="Open")})
    else:
        st.markdown(
            '<div class="stat"><div class="l">Not connected yet</div>'
            '<div class="h" style="font-size:1.3rem;margin-top:6px">Reach, profile visits, website clicks and where followers live</div>'
            '<div class="s" style="margin-top:6px">Needs a one-time connection to the official Instagram API by the account owner. '
            'Once connected, these figures refresh every Monday with the rest of the dashboard.</div></div>',
            unsafe_allow_html=True)

# --------------------------------------------------------------------------- #
# 3 · How we compare
# --------------------------------------------------------------------------- #
with T[2]:
    ui.head("Benchmark", "LCS and other Irish schools on Instagram",
            f"Last 8–12 posts per school · captured {datetime.fromisoformat(BM['captured']).strftime('%d %B %Y')}")
    scope = st.segmented_control("Compare with", ["Limerick schools", "Limerick + leading Irish schools"],
                                 default="Limerick schools") or "Limerick schools"
    df = schools if scope.startswith("Limerick +") else schools[schools["group"].isin(["LCS", "Limerick"])]
    df = df.assign(colour=df["group"].map({"LCS": GOLD, "Limerick": NAVY, "Ireland reference": "#9fb6d1"}))

    def hbar(data, x, title, fmt="{:,}", unit=""):
        d = data.sort_values(x)
        fig = go.Figure(go.Bar(x=d[x], y=d["short"], orientation="h", marker_color=d["colour"],
                               text=[fmt.format(v) + unit for v in d[x]], textposition="outside", cliponaxis=False,
                               hovertemplate="%{y}: %{x}<extra></extra>"))
        fig.update_xaxes(visible=False, range=[0, d[x].max() * 1.25])
        st.markdown(f"**{title}**")
        st.plotly_chart(ui.fig_style(fig, 34 * len(d) + 40, legend=False), width="stretch", config=CHART_CFG)

    a, b = st.columns(2)
    with a:
        hbar(df, "followers", "Followers")
    with b:
        hbar(df, "er", "Engagement rate", "{:.1f}", "%")
    a, b = st.columns(2)
    with a:
        hbar(df.assign(pw=df["per_week"].clip(upper=7)), "pw", "Posts per week", "{:.1f}")
    with b:
        hbar(df, "avg_eng", "Average interactions per post")
    st.markdown('<div class="small"><span style="color:#fdbc59">●</span> LCS &nbsp; <span style="color:#0b3767">●</span> Limerick schools'
                + (' &nbsp; <span style="color:#9fb6d1">●</span> Leading Irish schools' if scope.startswith("Limerick +") else "")
                + " &nbsp;·&nbsp; Posts per week capped at 7.</div>", unsafe_allow_html=True)

    st.write("")
    ui.head("What works", "Average interactions by type of post",
            "Other Irish schools in the sample (LCS excluded). Higher bars show what families respond to most.")
    rows = []
    for _, r in schools[schools["group"] != "LCS"].iterrows():
        for p, v in r["pillar_eng"].items():
            rows.append({"pillar": p, "eng": v, "n": r["pillars"].get(p, 0)})
    pdf = pd.DataFrame(rows)
    pdf["w"] = pdf["eng"] * pdf["n"]
    agg = pdf.groupby("pillar").agg(w=("w", "sum"), posts=("n", "sum")).reset_index()
    agg["eng"] = agg["w"] / agg["posts"].clip(lower=1)
    agg = agg[agg["posts"] >= 2].sort_values("eng")
    fig = go.Figure(go.Bar(x=agg["eng"], y=agg["pillar"], orientation="h",
                           marker_color=[PILLAR_COLORS.get(p, NAVY) for p in agg["pillar"]],
                           text=[f"{v:.0f}" for v in agg["eng"]], textposition="outside", cliponaxis=False,
                           customdata=agg["posts"], hovertemplate="%{y}: %{x:.0f} avg · %{customdata} posts<extra></extra>"))
    fig.update_xaxes(visible=False, range=[0, agg["eng"].max() * 1.2])
    w1, w2 = st.columns([1.4, 1])
    with w1:
        st.plotly_chart(ui.fig_style(fig, 300, legend=False), width="stretch", config=CHART_CFG)
    with w2:
        reel = schools[(schools["reels"] > 0) & (schools["avg_reel"] > 0)]
        st.markdown("**Reels vs photo posts**")
        fig = go.Figure()
        fig.add_bar(name="Reels", x=reel["short"], y=reel["avg_reel"], marker_color=NAVY)
        fig.add_bar(name="Photo posts", x=reel["short"], y=reel["avg_post"], marker_color=GRAY_LIGHT)
        fig.update_layout(barmode="group")
        st.plotly_chart(ui.fig_style(fig, 270), width="stretch", config=CHART_CFG)

    st.write("")
    ui.head("Best recent posts", "Strongest posts in the sample")
    top = sorted([(r["short"], *t) for _, r in schools.iterrows() for t in r["top"] if r["group"] != "LCS"], key=lambda x: -x[4])[:3]
    g = st.columns(3)
    for col, (name, code, kind, pillar, eng) in zip(g, top):
        with col:
            st.markdown(f'<div class="row-item"><span class="a">{esc(name)}</span><span class="pill">{eng} interactions</span></div>'
                        f'<div class="small" style="margin:6px 0 8px">{esc(kind)} · {esc(pillar)}</div>', unsafe_allow_html=True)
            path = "reel" if kind == "Reel" else "p"
            components.html(f'<iframe src="https://www.instagram.com/{path}/{code}/embed/" width="100%" height="520" frameborder="0" '
                            'scrolling="no" style="border:1px solid #e6e9ee;border-radius:12px;background:#fff"></iframe>', height=532)

    st.write("")
    k1, k2, k3 = st.columns(3)
    k1.markdown(ui.stat("Lesson 1", "Real moments", "School life and sport beat promotional posts across Irish schools."), unsafe_allow_html=True)
    k2.markdown(ui.stat("Lesson 2", "Reels for enrolment", "Laurel Hill's enrolment Reel earned 3.7× its average photo post."), unsafe_allow_html=True)
    k3.markdown(ui.stat("Lesson 3", "Consistency", "The most-followed schools post 3–6 times a week."), unsafe_allow_html=True)

# --------------------------------------------------------------------------- #
# 3 · Post ideas
# --------------------------------------------------------------------------- #
with T[3]:
    ui.head("Idea bank", "Post ideas for parents choosing a school",
            "Each idea shows an LCS strength: own-pace learning, small classes, Christian values, dedicated teachers.")
    f1, f2 = st.columns([1.3, 1])
    goal = f1.segmented_control("Goal", ["All", "Enrolment", "Trust", "Community"], default="All") or "All"
    fmt = f2.segmented_control("Format", ["All", "Reel", "Carousel", "Post", "Story"], default="All") or "All"
    pool = [i for i in ideas_for(segment)
            if (goal == "All" or i["goal"] == goal) and (fmt == "All" or i["format"] == fmt)
            ]
    if not pool:
        st.info("No ideas match these filters.")
    for k in range(0, len(pool), 3):
        cols = st.columns(3)
        for col, idea in zip(cols, pool[k:k + 3]):
            col.markdown(ui.post_card(f"{idea['format']} · {plat_label(idea['platform'])}", idea["title"], idea["hook"], idea["shots"],
                                      [(idea["goal"], "gold" if idea["goal"] == "Enrolment" else "dark"), (idea["pillar"], ""),
                                       (lvl(idea["segment"]), ""), (f"{idea['effort']} effort", "")],
                                      PILLAR_COLORS.get(idea["pillar"], NAVY)), unsafe_allow_html=True)
        st.write("")
    st.markdown('<div class="small">Photos of pupils only with written parental consent. Prefer hands, backs, work and wide shots, '
                'and never pair a full name with a face.</div>', unsafe_allow_html=True)

# --------------------------------------------------------------------------- #
# 4 · Calendar
# --------------------------------------------------------------------------- #
with T[4]:
    ui.head("2026/27", "School year at a glance", "Term dates follow the national standardised school year.")
    cal = pd.DataFrame(EDU["calendar"])
    cal["start"] = pd.to_datetime(cal["start"])
    cal["end"] = pd.to_datetime(cal["end"]) + pd.Timedelta(days=1)
    colours = {"term": "#c9d6e6", "holiday": GOLD, "faith": BURGUNDY_2, "enrol": NAVY}
    fig = px.timeline(cal, x_start="start", x_end="end", y="lane", color="kind", text="label",
                      color_discrete_map=colours, category_orders={"lane": ["School year", "Faith", "Enrolment"]})
    fig.update_traces(textposition="inside", insidetextanchor="middle", textfont=dict(size=11), marker_line_width=0)
    fig.update_yaxes(autorange="reversed", title=None)
    fig.update_xaxes(title=None, dtick="M1", tickformat="%b",
                     range=[pd.Timestamp(TODAY) - pd.Timedelta(days=5), pd.Timestamp("2027-06-30")])
    fig.add_shape(type="line", x0=pd.Timestamp(TODAY), x1=pd.Timestamp(TODAY), y0=0, y1=1, yref="paper",
                  line=dict(color="#530100", width=2))
    fig.update_layout(uniformtext_minsize=9, uniformtext_mode="hide")
    st.plotly_chart(ui.fig_style(fig, 260, legend=False), width="stretch", config=CHART_CFG)
    st.markdown('<div class="small"><span style="color:#0b3767">■</span> Enrolment focus &nbsp; <span style="color:#6d1717">■</span> Christian calendar &nbsp; '
                '<span style="color:#fdbc59">■</span> Holidays &nbsp; <span style="color:#c9d6e6">■</span> Term &nbsp; '
                '<span style="color:#530100">|</span> Today</div>', unsafe_allow_html=True)

    st.write("")
    ui.head("Coming up", "Key moments and what to post")
    by_title = {i["title"]: i for i in EDU["ideas"]}
    up = [m for m in EDU["moments"] if date.fromisoformat(m["date"]) >= TODAY]
    for k in range(0, len(up), 3):
        cols = st.columns(3)
        for col, m in zip(cols, up[k:k + 3]):
            d = date.fromisoformat(m["date"])
            idea = by_title.get(m["idea"], {})
            col.markdown(ui.post_card(f"{d.strftime('%a %d %b')} · in {(d - TODAY).days} days", m["name"],
                                      f"Post: {idea.get('title', m['idea'])}", idea.get("hook", ""),
                                      [(idea.get("format", ""), "dark"), (idea.get("pillar", ""), "")],
                                      PILLAR_COLORS.get(idea.get("pillar", ""), NAVY)), unsafe_allow_html=True)
        st.write("")

# --------------------------------------------------------------------------- #
# 5 · Trends
# --------------------------------------------------------------------------- #
with T[5]:
    reels = [dict(a) for a in (TRENDS.get("reels_audio") or {}).get("items", [])]
    for a in reels:
        a["opp"] = ins.opportunity(a)
    ie = (TRENDS.get("ireland_chart") or {}).get("items", [])
    t1, t2 = st.columns([1.2, 1])
    with t1:
        ui.head("Instagram", "Sounds trending this week",
                f"Week of {(TRENDS.get('reels_audio') or {}).get('week_label', '')}. Updated every Friday.")
        for a in sorted(reels, key=lambda x: -x["opp"]["score"])[:6]:
            st.markdown(f'<div class="row-item"><span><span class="a">{esc(a["title"])}</span><br>'
                        f'<span class="b">{esc(a["artist"])} · {esc(a.get("trend", ""))}</span></span>'
                        f'<span class="pill">{esc(a["opp"]["label"])}</span></div>', unsafe_allow_html=True)
        st.markdown('<div class="small" style="margin-top:8px">School accounts may not be able to use chart songs. '
                    'If not, use an instrumental from the Reels library or a voiceover.</div>', unsafe_allow_html=True)
    with t2:
        ui.head("Ireland", "Climbing the Irish charts", "Songs gaining fastest on Spotify Ireland.")
        ris = []
        for i in ie[:50]:
            ch = ins.parse_change(i.get("change"))
            if ch and ch > 0:
                ris.append({"song": f"{i['title']} · {i['artist']}", "climb": ch})
        rdf = pd.DataFrame(ris).sort_values("climb", ascending=False).head(7) if ris else pd.DataFrame()
        if not rdf.empty:
            r2 = rdf.iloc[::-1]
            fig = go.Figure(go.Bar(x=r2["climb"], y=r2["song"], orientation="h", marker_color=NAVY,
                                   text=[f"+{v}" for v in r2["climb"]], textposition="outside", cliponaxis=False))
            fig.update_xaxes(visible=False, range=[0, rdf["climb"].max() * 1.2])
            st.plotly_chart(ui.fig_style(fig, 300, legend=False), width="stretch", config=CHART_CFG)

    st.write("")
    ui.head("Hashtags", "Sets for school posts", "Instagram allows up to 5 hashtags per post: pick one from each set.")
    show_sets = {k: v for k, v in EDU["hashtags"].items() if segment == "All" or k not in ({"Primary", "Secondary"} - {segment})}
    hc = st.columns(len(show_sets))
    for col, (k, tags) in zip(hc, show_sets.items()):
        col.markdown(f"**{k}**<br>" + ui.chips(tags), unsafe_allow_html=True)

# --------------------------------------------------------------------------- #
# 6 · Caption builder
# --------------------------------------------------------------------------- #
with T[6]:
    ui.head("Write", "Copy lab", "Two tools: get new caption ideas, or improve a caption you already wrote.")

    def score_block(sc: dict, title: str = "Reach score", tips: bool = True) -> str:
        col = NAVY if sc["score"] >= 62 else GOLD_DEEP if sc["score"] >= 45 else BURGUNDY_2
        bars = "".join(
            f'<div style="display:flex;align-items:center;gap:8px;margin:4px 0"><div style="width:112px;font-size:.76rem;color:#7a808a">{k}</div>'
            f'<div style="flex:1;height:6px;background:#eef1f5;border-radius:4px;overflow:hidden"><div style="width:{v / m * 100:.0f}%;height:100%;background:{col}"></div></div>'
            f'<div style="width:38px;text-align:right;font-size:.74rem;font-weight:700">{v}/{m}</div></div>' for k, (v, m) in sc["parts"].items())
        tip = "".join(f'<div class="small" style="margin-top:4px">→ {esc(t)}</div>' for t in sc["tips"]) if tips else ""
        return (f'<div class="stat"><div class="l">{esc(title)}</div><div style="display:flex;align-items:baseline;gap:10px">'
                f'<div class="v" style="color:{col}">{sc["score"]}<small>/100</small></div><div style="font-weight:800;color:{col};font-size:.9rem">{esc(sc["label"])}</div></div>'
                f'{bars}{tip}</div>')

    def algo_panel(fmt: str) -> None:
        a = copylab.ALGO[fmt]
        sig = "".join(f'<div class="row-item"><span class="a">{i + 1}. {esc(x)}</span></div>' for i, x in enumerate(a["signals"]))
        tips = "".join(f'<div class="small" style="margin-top:6px">→ {esc(t)}</div>' for t in a["tips"])
        st.markdown(f'<div class="stat"><div class="l">How Instagram ranks a {esc(fmt.lower())}</div>'
                    f'<div class="s" style="margin:4px 0 6px">Shown to: <b>{esc(a["reach"])}</b></div>{sig}{tips}</div>', unsafe_allow_html=True)

    def tags_block(tags: list[str], key: str) -> None:
        st.markdown('<div class="eyebrow" style="margin-top:10px">Hashtags to use</div>' + ui.chips(tags), unsafe_allow_html=True)
        st.code(" ".join(tags), language=None, wrap_lines=True)

    mode = st.segmented_control("Tool", ["Get caption ideas", "Improve my caption"], default="Get caption ideas", key="lab_mode",
                                label_visibility="collapsed") or "Get caption ideas"
    st.write("")

    if mode == "Get caption ideas":
        st.markdown('<div class="insight"><div class="n">1</div><div class="t"><b>Get caption ideas.</b> Tell us what the post is about. '
                    'You get three ready-to-post captions, ranked by reach score, each with its own hashtags.</div></div>', unsafe_allow_html=True)
        a1, a2, a3 = st.columns([2, 1, 1])
        topic_txt = a1.text_input("What is the post about?", placeholder="e.g. Enrolment for secondary · Christmas service · Meet the teacher", key="idea_topic")
        idea_fmt = a2.selectbox("Format", copylab.FORMATS, key="idea_fmt")
        idea_detail = a3.text_input("Detail (optional)", placeholder="Thu 20 Nov · 10am", key="idea_detail")
        algo_panel(idea_fmt)
        st.write("")
        quick = st.pills("Or pick a topic", ["Enrolment", "Open morning", "Christmas", "Easter", "Faith", "Meet the teacher", "Learning at own pace",
                                              "Achievements", "School event", "Parent testimonial"], key="idea_quick")
        if st.button("Get 3 caption ideas", type="primary", key="idea_go"):
            q = topic_txt.strip() or (quick or "")
            if q:
                st.session_state["lab_ideas"] = copylab.ideas(q, segment, platform, idea_detail, idea_fmt)
            else:
                st.warning("Type a topic or pick one above.")
        res = st.session_state.get("lab_ideas")
        if res:
            st.write("")
            cols = st.columns(3)
            for k, (col, v) in enumerate(zip(cols, res)):
                sc = v["score"]
                with col:
                    st.markdown(f'<div class="eyebrow">{"Best pick · " if k == 0 else f"Option {k + 1} · "}{esc(v["style"])} · '
                                f'{esc(v["format"])}</div>', unsafe_allow_html=True)
                    st.code(v["body"], language=None, wrap_lines=True)
                    tags_block(v["tags"], f"t{k}")
                    st.markdown(score_block(sc, tips=False), unsafe_allow_html=True)
                    st.download_button("Download", (v["body"] + "\n\n" + " ".join(v["tags"])).encode(), f"caption-{k + 1}.txt",
                                       key=f"dl_idea_{k}", width="stretch")

    else:
        st.markdown('<div class="insight"><div class="n">2</div><div class="t"><b>Improve my caption.</b> Paste a caption you wrote. '
                    'We keep your message, strengthen the first line and the call to action, fix the hashtags and show the score before and after.</div></div>',
                    unsafe_allow_html=True)
        b1, b2 = st.columns([3, 1])
        mine = b1.text_area("Your caption", height=140, key="imp_text",
                            placeholder="Paste your caption here, with or without hashtags…")
        imp_fmt = b2.selectbox("Format", copylab.FORMATS, key="imp_fmt")
        b2.write("")
        go = b2.button("Improve caption", type="primary", key="imp_go", width="stretch")
        algo_panel(imp_fmt)
        if go:
            if mine.strip():
                st.session_state["lab_imp"] = copylab.improve(mine, segment, platform, imp_fmt)
            else:
                st.warning("Paste a caption first.")
        r = st.session_state.get("lab_imp")
        if r:
            st.write("")
            bb, aa = r["before"]["score"], r["after"]["score"]
            k1, k2, k3 = st.columns(3)
            k1.markdown(ui.stat("Before", bb, esc(r["before"]["label"]), unit="/100"), unsafe_allow_html=True)
            k2.markdown(ui.stat("After", aa, esc(r["after"]["label"]), unit="/100", accent=True), unsafe_allow_html=True)
            k3.markdown(ui.stat("Improvement", f"{aa - bb:+d}", "points"), unsafe_allow_html=True)
            st.write("")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown('<div class="eyebrow">Your caption</div>', unsafe_allow_html=True)
                st.code(r["original"], language=None, wrap_lines=True)
                st.markdown(score_block(r["before"], "Score before"), unsafe_allow_html=True)
            with c2:
                st.markdown('<div class="eyebrow">Improved caption</div>', unsafe_allow_html=True)
                st.code(r["body"], language=None, wrap_lines=True)
                tags_block(r["tags"], "imp")
                st.markdown("".join(f'<div class="small">✓ {esc(c)}</div>' for c in r["changes"]), unsafe_allow_html=True)
                st.write("")
                st.markdown(score_block(r["after"], "Score after"), unsafe_allow_html=True)
                st.download_button("Download improved caption", (r["body"] + "\n\n" + " ".join(r["tags"])).encode(), "improved-caption.txt",
                                   key="dl_imp", width="stretch")

    st.markdown('<div class="small" style="margin-top:18px">Reach score follows Instagram\'s published ranking signals for each format '
                '(attention, DM sends, likes and comments, saves, search keywords, originality, max 5 hashtags). It is an estimate, not a guarantee.</div>',
                unsafe_allow_html=True)

with st.sidebar:
    st.markdown(f"**{APP_NAME}**  \nDeveloper: {DEVELOPER}")
    st.caption(f"Benchmark: Instagram, {len(schools)} Irish schools, captured {BM['captured']} (refreshed on request). "
               "Trends: CreatorDB, SocialPilot, Kworb, updated every Friday. Timing: Buffer 2026 (Instagram), "
               "Sprout Social 2026 education data (Facebook).")

st.markdown(f'<div class="foot"><b>{APP_NAME}</b> · Limerick Christian School · Developer: <b>{DEVELOPER}</b></div>',
            unsafe_allow_html=True)
