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

import insights as ins
import studio
import ui
from ui import BURGUNDY_2, CHART_CFG, GOLD, GRAY_LIGHT, NAVY, OFF_WHITE, esc

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
lcs = schools[schools["group"] == "LCS"].iloc[0]
lim = schools[schools["group"] == "Limerick"]
lim_avg = {"followers": int(lim["followers"].mean()), "er": round(lim["er"].mean(), 1), "pw": round(lim["per_week"].mean(), 1)}

# --------------------------------------------------------------------------- #
# Masthead + controls
# --------------------------------------------------------------------------- #
week_start = TODAY - timedelta(days=TODAY.weekday())
st.markdown(
    f"""<div class="mast"><div class="mast-row">
<div><div class="brand">LCS <span>·</span> IDEAs for Posting</div>
<div class="sub">Social media planning · Limerick Christian School</div></div>
<div class="meta">Week of <b>{week_start.strftime('%d %B %Y')}</b><br>Prepared for the Principal<br>Developer: <b>{DEVELOPER}</b></div>
</div><div class="rule"></div></div>""",
    unsafe_allow_html=True,
)

c1, c2, _ = st.columns([1.1, 1.1, 2])
segment = c1.segmented_control("School level", ["All", "Primary", "Secondary"], default="All") or "All"
platform = c2.segmented_control("Platform", ["Instagram", "Facebook"], default="Instagram") or "Instagram"


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


T = st.tabs(["This week", "How we compare", "Post ideas", "Calendar", "Trends", "Caption builder"])

# --------------------------------------------------------------------------- #
# 1 · This week
# --------------------------------------------------------------------------- #
with T[0]:
    deadline = date.fromisoformat(EDU["school"]["promo_deadline"]["date"])
    days_left = (deadline - TODAY).days
    s = st.columns(4)
    s[0].markdown(ui.stat("Instagram followers", f"{int(lcs.followers):,}",
                          f"Limerick schools average {lim_avg['followers']:,}"), unsafe_allow_html=True)
    s[1].markdown(ui.stat("Engagement rate", lcs.er, f'<span class="up">{lcs.er / lim_avg["er"]:.0f}× the local average</span> · small, loyal audience',
                          unit="%", accent=True), unsafe_allow_html=True)
    s[2].markdown(ui.stat("Posts per week", lcs.per_week, f'<span class="down">Local schools post {lim_avg["pw"]} a week</span>'),
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
# 2 · How we compare
# --------------------------------------------------------------------------- #
with T[1]:
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
with T[2]:
    ui.head("Idea bank", "Post ideas for parents choosing a school",
            "Each idea shows an LCS strength: own-pace learning, small classes, Christian values, dedicated teachers.")
    f1, f2 = st.columns([1.3, 1])
    goal = f1.segmented_control("Goal", ["All", "Enrolment", "Trust", "Community"], default="All") or "All"
    fmt = f2.segmented_control("Format", ["All", "Reel", "Carousel", "Photo", "Story"], default="All") or "All"
    pool = [i for i in ideas_for(segment)
            if (goal == "All" or i["goal"] == goal) and (fmt == "All" or i["format"] == fmt)
            and (i["platform"] in ("Both", platform))]
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
with T[3]:
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
with T[4]:
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
    ui.head("Hashtags", "Sets for school posts", "Instagram: 8–12 tags. Facebook: 1–3 tags or none.")
    hc = st.columns(5)
    for col, (k, tags) in zip(hc, EDU["hashtags"].items()):
        col.markdown(f"**{k}**<br>" + ui.chips(tags), unsafe_allow_html=True)

# --------------------------------------------------------------------------- #
# 6 · Caption builder
# --------------------------------------------------------------------------- #
with T[5]:
    ui.head("Write", "Caption builder", "Pick an idea and get a ready-to-post caption with the right hashtags.")
    b1, b2 = st.columns([1, 1.3])
    with b1:
        pool = ideas_for(segment)
        idea = st.selectbox("Idea", pool, format_func=lambda i: f"{i['title']} · {lvl(i['segment'])}")
        tone = st.segmented_control("Tone", ["Warm", "Professional", "Joyful"], default="Warm") or "Warm"
        detail = st.text_input("Add a detail (optional)", placeholder="e.g. Open morning, Thursday 20 Nov, 10am")
    with b2:
        opener = "✨ " if tone == "Joyful" else ""
        strength = {"Student life": "At LCS every pupil learns at their own pace, in small classes, with teachers who know them well.",
                    "Faith & values": "Christian values shape every school day, from chapel to the classroom.",
                    "Enrolment": "Applications are open for primary and secondary pupils.",
                    "Teachers": "Our dedicated teachers know every pupil by name.",
                    "Parents": "We work alongside families every step of the way.",
                    "Achievement": "Progress is celebrated here, at every pace.",
                    "Events": "School is a community, and days like this show it."}.get(idea["pillar"], "")
        if tone == "Professional":
            strength = strength.replace("At LCS", "At Limerick Christian School")
        cta = {"Book a visit": "Book a visit: link in bio.", "Apply now": "Apply now: link in bio.",
               "Register for a visit": "Register on our Events page."}.get(idea["cta"], idea["cta"] + ".")
        if platform == "Facebook":
            cta = cta.replace("link in bio", "limerickchristianschool.com")
        seg_tags = EDU["hashtags"]["Primary" if idea["segment"] == "Primary" else "Secondary"]
        tags = seg_tags[:3] + EDU["hashtags"]["Faith"][:2] + EDU["hashtags"]["Local"][:3] + EDU["hashtags"]["Parents"][:1]
        tags = tags[:3] if platform == "Facebook" else tags[:10]
        caption = f"{opener}{idea['hook']}\n\n{strength}" + (f"\n\n{detail}" if detail else "") + f"\n\n{cta}\n\n" + " ".join(tags)
        st.code(caption, language=None, wrap_lines=True)
        r = studio.check_caption(caption, EDU["hashtags"]["Local"])
        c = st.columns(3)
        c[0].markdown(ui.stat("Caption score", r["score"], "out of 100", accent=True), unsafe_allow_html=True)
        c[1].markdown(ui.stat("Words", r["words"], "30–150 works best"), unsafe_allow_html=True)
        c[2].markdown(ui.stat("Hashtags", r["hashtags"], "IG 8–12 · FB 1–3"), unsafe_allow_html=True)
        st.write("")
        st.download_button("Download caption", caption.encode(), f"{idea['id']}-caption.txt", width="stretch")

with st.sidebar:
    st.markdown(f"**{APP_NAME}**  \nDeveloper: {DEVELOPER}")
    st.caption(f"Benchmark: Instagram, {len(schools)} Irish schools, captured {BM['captured']} (refreshed on request). "
               "Trends: CreatorDB, SocialPilot, Kworb, updated every Friday. Timing: Buffer 2026 (Instagram), "
               "Sprout Social 2026 education data (Facebook).")

st.markdown(f'<div class="foot"><b>{APP_NAME}</b> · Limerick Christian School · Developer: <b>{DEVELOPER}</b></div>',
            unsafe_allow_html=True)
