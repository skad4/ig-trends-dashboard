"""Instagram Trends Intelligence — Limerick · Ireland
Free, weekly-updated "Creative Center"-style dashboard for Instagram.
Run: streamlit run app.py
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

import insights as ins
import studio
import ui
from ui import BURGUNDY_2, GOLD, GRAY, NAVY, NAVY_2, OFF_WHITE, esc

ROOT = Path(__file__).parent
DATA, HISTORY = ROOT / "data", ROOT / "data" / "history"

APP_NAME, DEVELOPER = "LCS – IDEAs for Posting", "Ed Trigueros"
st.set_page_config(page_title=APP_NAME, page_icon="📊", layout="wide")
ui.inject_css()


# --------------------------------------------------------------------------- #
# Data
# --------------------------------------------------------------------------- #
@st.cache_data(ttl=3600)
def load_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def secret(name: str) -> str | None:
    try:
        v = st.secrets.get(name)
        if v:
            return v
    except Exception:  # noqa: BLE001  (no secrets file locally)
        pass
    return os.getenv(name)


TAGS = load_json(str(ROOT / "config" / "hashtags.json"))
INS = load_json(str(ROOT / "config" / "insights.json"))
CATS, REGIONS = TAGS["categories"], TAGS["regions"]
LOCAL = REGIONS["Limerick +50km"]

files = sorted(HISTORY.glob("*.json"), reverse=True)

with st.sidebar:
    st.markdown(f'<div class="sb-brand">{APP_NAME}</div><div class="sb-sub">Instagram trends · Limerick · Ireland</div>',
                unsafe_allow_html=True)
    st.markdown(f'<div class="small" style="margin:-4px 0 10px">Developer: <b>{DEVELOPER}</b></div>',
                unsafe_allow_html=True)
    region = st.segmented_control("Market", ["Limerick +50km", "Ireland", "Global"], default="Limerick +50km",
                                  format_func=lambda r: {"Limerick +50km": "📍 Limerick", "Ireland": "🇮🇪 Ireland", "Global": "🌍 Global"}[r]) or "Limerick +50km"
    category = st.selectbox("Category", list(CATS.keys()), index=0,
                            format_func=lambda c: f"{CATS[c].get('icon','')}  {c}")
    week_opts = {f.stem: f for f in files} or {"latest": DATA / "latest.json"}
    week_key = st.selectbox("Weekly snapshot", list(week_opts.keys()), index=0)
    st.divider()
    has_key = bool(secret("GEMINI_API_KEY"))
    st.markdown(
        f'<div class="small">Auto-refresh: <b>every Friday</b><br>AI engine: <b>{"Gemini · connected" if has_key else "Template mode"}</b>'
        f'<br>Sources: CreatorDB · SocialPilot · Kworb · Buffer<br><br>{APP_NAME}<br>Developer: <b>{DEVELOPER}</b></div>', unsafe_allow_html=True)

D = load_json(str(week_opts[week_key]))
prev_file = next((f for f in files if f.stem < week_key), None)
P = load_json(str(prev_file)) if prev_file else None
A = D.get("analysis") or {}
AI_CATS = A.get("categories", {})
reels = [dict(a) for a in (D.get("reels_audio") or {}).get("items", [])]
biz = (D.get("business_audio") or {}).get("items", [])
ie = (D.get("ireland_chart") or {}).get("items", [])
BIZ_BY_TITLE = {b["title"].lower(): b for b in biz}
prev_heat = {a["title"].lower(): a.get("heat") for a in ((P or {}).get("reels_audio") or {}).get("items", [])}

for a in reels:
    a["opp"] = ins.opportunity(a)
    a["why"] = ins.audio_categories(a, BIZ_BY_TITLE, {**AI_CATS, "_kind": (A.get("_meta") or {}).get("kind")}, INS["audio_category_keywords"])
    a["cats"] = sorted(a["why"])

cat_ai = AI_CATS.get(category, {})
cat_cfg = CATS[category]
cat_audios = sorted([a for a in reels if category in a["cats"]], key=lambda a: -a["opp"]["score"]) or reels[:3]
local_tags = LOCAL["core"] if region == "Limerick +50km" else REGIONS["Ireland"]["core"] if region == "Ireland" else []
slots = ins.next_slots(INS["posting_times"], n=3)


def fmt_num(n) -> str:
    if n is None or (isinstance(n, float) and pd.isna(n)):
        return "–"
    n = float(n)
    return f"{n/1e6:.1f}M" if n >= 1e6 else f"{n/1e3:.0f}K" if n >= 1e3 else f"{n:.0f}"


# --------------------------------------------------------------------------- #
# Hero + KPIs
# --------------------------------------------------------------------------- #
week_label = (D.get("reels_audio") or {}).get("week_label") or D.get("week", "")
st.markdown(
    f"""<div class="hero"><div class="eyebrow">Weekly Instagram intelligence · Developer: Ed Trigueros</div>
<h1>{esc(APP_NAME)}</h1>
<p><b>What to post this week:</b> trending audio, hashtags, video formats and ready-to-use scripts for <b>{esc(category)}</b>, focused on <b>{esc(region)}</b>.</p>
<div class="pills"><span class="pill gold">Week of {esc(week_label)}</span><span class="pill">Updated {esc(D.get('updated_at','')[:10])}</span>
<span class="pill">{len(reels)} sounds tracked</span><span class="pill">{len(CATS)} categories</span></div></div>""",
    unsafe_allow_html=True,
)

top = reels[0] if reels else {}
best_opp = max(reels, key=lambda a: a["opp"]["score"]) if reels else {}
ie_top = ie[0] if ie else {}
nd = ins.upcoming_dates(INS["key_dates"], category, n=1)
k = st.columns(5)
k[0].markdown(ui.kpi("#1 Reels sound", top.get("title", "–"), f"{top.get('artist','')} · Heat {top.get('heat','–')}"), unsafe_allow_html=True)
k[1].markdown(ui.kpi("Best opportunity", best_opp.get("title", "–"),
                     f"Score {best_opp.get('opp',{}).get('score','–')} · {best_opp.get('opp',{}).get('label','')}"), unsafe_allow_html=True)
k[2].markdown(ui.kpi("#1 Spotify Ireland", ie_top.get("title", "–"), ie_top.get("artist", "")), unsafe_allow_html=True)
k[3].markdown(ui.kpi("Next best slot", ins.fmt_slot(slots[0]["dt"]) if slots else "–",
                     f"{slots[0]['tier']} engagement day" if slots else ""), unsafe_allow_html=True)
k[4].markdown(ui.kpi("Next key date", nd[0]["name"] if nd else "–", f"in {nd[0]['days']} days" if nd else ""), unsafe_allow_html=True)
st.write("")

T = st.tabs(["Overview", "What to Post", "Trending Audio", "Hashtags", "Sound & Video Examples",
             "Script & Copy Studio", "Limerick Local", "Sources"])

# --------------------------------------------------------------------------- #
# 1 · Overview
# --------------------------------------------------------------------------- #
with T[0]:
    c1, c2 = st.columns([1.15, 1])
    with c1:
        ui.section("This week in one minute")
        st.markdown(f'<div class="card soft">{esc(A.get("week_summary","No analysis yet."))}</div>', unsafe_allow_html=True)
        for t in A.get("key_takeaways", []):
            st.markdown(f"- {t}")
        if A.get("ireland_signal"):
            st.markdown(f'<div class="card navy"><b>🇮🇪 Ireland signal</b><div class="row">{esc(A["ireland_signal"])}</div></div>',
                        unsafe_allow_html=True)
    with c2:
        ui.section("Opportunity matrix", "Heat vs saturation. Top-left = trending but not yet crowded.")
        if reels:
            df = pd.DataFrame([{"title": a["title"], "artist": a["artist"], "heat": a.get("heat") or 0,
                                "score": a["opp"]["score"], "status": a["opp"]["label"],
                                "reels_plot": a.get("reels") or 30000} for a in reels])
            top_titles = set(df.nlargest(7, "score")["title"])
            df["label"] = df["title"].where(df["title"].isin(top_titles), "")
            fig = px.scatter(df, x="reels_plot", y="heat", size="score", color="status", text="label", log_x=True,
                             color_discrete_map={"Use now": NAVY, "Ride the wave": GOLD, "Saturated": BURGUNDY_2, "Early · watch": GRAY},
                             labels={"reels_plot": "Reels already using it (log scale)", "heat": "Heat"},
                             hover_data={"title": True, "artist": True, "reels_plot": False, "score": True, "label": False}, size_max=26)
            fig.update_traces(textposition="top center", textfont_size=10, marker=dict(line=dict(width=1, color="white")))
            fig.add_hline(y=55, line_dash="dot", line_color="rgba(11,55,103,.35)")
            st.plotly_chart(ui.plotly_layout(fig, 410), width="stretch", config={"displayModeBar": False})

    c3, c4 = st.columns(2)
    with c3:
        ui.section("Opportunities")
        for t in A.get("opportunities", []):
            st.markdown(f"- {t}")
    with c4:
        ui.section("Watch out")
        for t in A.get("watch_out", []):
            st.markdown(f"- {t}")
    # ---------------- Business-intelligence widgets ----------------
    st.write("")
    ui.section("Trend intelligence", "Business-intelligence view of this week's signals: lifecycle, demand by category, themes and what's rising next.")
    n = len(reels) or 1
    rising_n = sum("ris" in (a.get("momentum") or "").lower() for a in reels)
    reels_only = sum("reels only" in (a.get("also_charting") or "").lower() for a in reels)
    overlap = sum(1 for a in reels if a.get("ireland_pos"))
    med_reels = pd.Series([a.get("reels") for a in reels if a.get("reels")]).median() if reels else None
    avg_heat = round(sum(a.get("heat") or 0 for a in reels) / n)
    m = st.columns(5)
    m[0].markdown(ui.kpi("Average heat", avg_heat, "across tracked sounds"), unsafe_allow_html=True)
    m[1].markdown(ui.kpi("Rising share", f"{rising_n / n:.0%}", f"{rising_n} of {len(reels)} sounds"), unsafe_allow_html=True)
    m[2].markdown(ui.kpi("Instagram-native", f"{reels_only / n:.0%}", "trend only on Reels, not music charts"), unsafe_allow_html=True)
    m[3].markdown(ui.kpi("Ireland overlap", f"{overlap / n:.0%}", f"{overlap} sounds also chart in IE"), unsafe_allow_html=True)
    m[4].markdown(ui.kpi("Median saturation", fmt_num(med_reels), "reels per trending sound"), unsafe_allow_html=True)
    st.write("")

    g1, g2, g3 = st.columns(3)
    with g1:
        st.markdown("**Trend lifecycle**")
        life = pd.Series([a.get("momentum") or "Unknown" for a in reels]).value_counts().reset_index()
        life.columns = ["stage", "sounds"]
        fig = px.pie(life, names="stage", values="sounds", hole=.62,
                     color="stage", color_discrete_map={"Rising": NAVY, "Returning": GOLD, "Peak": BURGUNDY_2, "Unknown": GRAY})
        fig.update_traces(textinfo="value", textfont_size=13, marker=dict(line=dict(color="white", width=2)))
        fig.update_layout(annotations=[dict(text=f"{len(reels)}<br>sounds", showarrow=False, font=dict(size=15, color=NAVY))])
        st.plotly_chart(ui.plotly_layout(fig, 280), width="stretch", config={"displayModeBar": False})
        st.caption("Rising = early, best time to jump in. Returning/Peak = seasonal or crowded.")
    with g2:
        st.markdown("**Trend fuel by category**")
        fuel = [{"category": c, "fuel": sum(a["opp"]["score"] for a in reels if c in a["cats"]),
                 "sounds": sum(1 for a in reels if c in a["cats"])} for c in CATS]
        fdf = pd.DataFrame(fuel).sort_values("fuel")
        fdf["sel"] = fdf["category"].eq(category).map({True: "Selected", False: "Other"})
        fig = px.bar(fdf, x="fuel", y="category", orientation="h", color="sel", text="sounds",
                     color_discrete_map={"Selected": GOLD, "Other": NAVY}, labels={"fuel": "Sum of opportunity scores", "category": ""})
        fig.update_traces(texttemplate="%{text}", textposition="outside", cliponaxis=False)
        fig.update_layout(showlegend=False)
        fig.update_xaxes(range=[0, max(fdf["fuel"].max(), 1) * 1.18])
        st.plotly_chart(ui.plotly_layout(fig, 300), width="stretch", config={"displayModeBar": False})
        st.caption("Bar = total opportunity of sounds recommended for each category · label = number of sounds.")
    with g3:
        st.markdown("**Top content themes**")
        th = pd.DataFrame(ins.theme_counts(reels, biz, INS.get("content_themes", {})))
        if not th.empty:
            fig = px.bar(th.sort_values("mentions"), x="mentions", y="theme", orientation="h",
                         color_discrete_sequence=[NAVY_2], labels={"mentions": "Mentions in this week's trends", "theme": ""})
            st.plotly_chart(ui.plotly_layout(fig, 300), width="stretch", config={"displayModeBar": False})
        st.caption("Formats and moods that repeat across trending sounds and content ideas.")

    g4, g5 = st.columns([1.2, 1])
    with g4:
        st.markdown("**Fastest risers in Ireland · next-up watchlist**")
        ris = []
        reels_titles = {a["title"].lower() for a in reels}
        for i in ie[:50]:
            ch = ins.parse_change(i.get("change"))
            if ch and ch > 0:
                ris.append({"song": f"{i['artist']} — {i['title']}", "climb": ch, "pos": i["pos"],
                            "status": "Already on Reels" if i["title"].lower() in reels_titles else "Not on Reels yet"})
        rdf = pd.DataFrame(ris).sort_values("climb", ascending=False).head(10) if ris else pd.DataFrame()
        if not rdf.empty:
            fig = px.bar(rdf.iloc[::-1], x="climb", y="song", orientation="h", color="status",
                         color_discrete_map={"Not on Reels yet": GOLD, "Already on Reels": NAVY},
                         hover_data={"pos": True}, labels={"climb": "Places climbed this week (Spotify IE)", "song": ""})
            ui.plotly_layout(fig, 380)
            fig.update_layout(legend=dict(orientation="h", y=-0.22, x=0), margin=dict(t=10, b=10))
            st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
            st.caption("Gold = climbing fast in Ireland but not yet a Reels trend. These are candidates to use early.")
    with g5:
        st.markdown("**Week-over-week movers**")
        if P:
            prev = {a["title"].lower(): a for a in (P.get("reels_audio") or {}).get("items", [])}
            mv = []
            for a in reels:
                pa = prev.get(a["title"].lower())
                mv.append({"Sound": a["title"], "Heat": a.get("heat"),
                           "Δ Heat": (a.get("heat") or 0) - (pa.get("heat") or 0) if pa else None,
                           "Status": "Returning" if pa else "🆕 New"})
            st.dataframe(pd.DataFrame(mv).sort_values("Δ Heat", ascending=False, na_position="first"), hide_index=True,
                         width="stretch", height=330)
        else:
            st.markdown('<div class="card soft small">History builds every Friday. From next week this panel compares each sound\'s heat '
                        'with the week before, plus new entries and drop-offs.</div>', unsafe_allow_html=True)
            sig = pd.DataFrame([{"Sound": a["title"], "Heat": a.get("heat"), "Opportunity": a["opp"]["score"],
                                 "Signal": a["opp"]["label"]} for a in reels]).sort_values("Opportunity", ascending=False)
            st.dataframe(sig, hide_index=True, width="stretch", height=280)

    meta = A.get("_meta", {})
    st.caption(f"Analysis: {meta.get('model','–')} · {meta.get('generated_at','')[:10]}"
               + (" · seed analysis, replaced on the first automatic run" if meta.get("kind") == "seed" else ""))

# --------------------------------------------------------------------------- #
# 2 · What to post
# --------------------------------------------------------------------------- #
with T[1]:
    ui.section(f"Your recommended post · {category}", "Everything in one brief: format, audio, time, hashtags and copy.")
    rec_audio = cat_audios[0] if cat_audios else {}
    rec_tags = list(dict.fromkeys((cat_ai.get("hashtags") or cat_cfg["mid"][:5]) + (cat_ai.get("new_hashtags") or [])))
    if region != "Global":
        rec_tags = list(dict.fromkeys(rec_tags + local_tags[:2]))
    rec_copy = (cat_ai.get("sample_copies") or [""])[0]
    b1, b2 = st.columns([1.2, 1])
    with b1:
        audio_txt = cat_ai.get("suggested_audio") or f"{rec_audio.get('title','')} — {rec_audio.get('artist','')}"
        st.markdown(
            f"""<div class="card navy"><h4>{esc(cat_ai.get('headline','Post idea'))}</h4>
<div class="row"><b>🎬 Format:</b> {esc((cat_ai.get('video_formats') or [cat_ai.get('content_idea','')])[0])}</div>
<div class="row"><b>💡 Idea:</b> {esc(cat_ai.get('content_idea',''))}</div>
<div class="row"><b>🎵 Audio:</b> {esc(audio_txt)}</div>
<div class="row"><b>🕒 Post at:</b> {esc(ins.fmt_slot(slots[0]['dt']) if slots else '')}</div></div>""",
            unsafe_allow_html=True)
        st.markdown(ui.chips(rec_tags, hot=cat_ai.get("hashtags", []), new=cat_ai.get("new_hashtags", [])), unsafe_allow_html=True)
        st.code(f"{rec_copy}\n\n{' '.join(rec_tags)}", language=None, wrap_lines=True)
    with b2:
        st.markdown("**Next best posting slots** (Irish time)")
        for s in slots:
            st.markdown(f'<div class="date-row"><span class="n">{esc(ins.fmt_slot(s["dt"]))}</span><span class="c">{esc(s["tier"])}</span></div>',
                        unsafe_allow_html=True)
        st.write("")
        st.markdown("**Upcoming key dates**")
        for d in ins.upcoming_dates(INS["key_dates"], category, n=5):
            st.markdown(f'<div class="date-row"><span><span class="n">{esc(d["name"])}</span><br><span class="small">{d["d"].strftime("%a %d %b %Y")}</span></span>'
                        f'<span class="c">{d["days"]} days</span></div>', unsafe_allow_html=True)

    st.write("")
    h1, h2 = st.columns([1.25, 1])
    with h1:
        ui.section("Best time to post", "Relative engagement by day and hour, based on Buffer's 2026 study of 9.6M posts (local time).")
        g = ins.heat_grid(INS["posting_times"])
        piv = g.pivot(index="day", columns="hour", values="score").reindex([d[:3] for d in ins.DAYS])
        fig = go.Figure(go.Heatmap(z=piv.values, x=[f"{h}:00" for h in piv.columns], y=list(piv.index),
                                   colorscale=[[0, OFF_WHITE], [0.45, "#c9d6e6"], [0.75, NAVY_2], [1, NAVY]],
                                   showscale=False, hovertemplate="%{y} %{x}<br>Score %{z}<extra></extra>", xgap=2, ygap=2))
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(ui.plotly_layout(fig, 300), width="stretch", config={"displayModeBar": False})
        st.caption(" · ".join(INS["posting_times"]["notes"]))
    with h2:
        ui.section("Weekly content plan", f"Posts for {category} on the strongest days of the next 7.")
        plan = ins.weekly_plan(category, cat_ai, cat_cfg, cat_audios, INS["posting_times"], local_tags)
        st.dataframe(plan, hide_index=True, width="stretch", height=230)
        st.download_button("Download plan (CSV)", plan.to_csv(index=False).encode(),
                           f"content-plan-{category.lower().replace(' ','-').replace('&','and')}.csv", "text/csv", width="stretch")

# --------------------------------------------------------------------------- #
# 3 · Trending audio
# --------------------------------------------------------------------------- #
with T[2]:
    view = st.segmented_control("View", ["Instagram Reels", "Ireland charts", "By business type"],
                                default="Ireland charts" if region == "Ireland" else "Instagram Reels") or "Instagram Reels"
    if view == "Instagram Reels":
        ui.section("Trending Reels audio", "Opportunity = Heat adjusted for saturation. 🇮🇪 = also in Spotify Ireland's weekly chart.")
        only = st.toggle(f"Only sounds that fit {category}", value=False)
        for a in [x for x in reels if not only or category in x["cats"]]:
            ph = prev_heat.get(a["title"].lower())
            delta = f" · {a['heat'] - ph:+d} vs last week" if ph is not None and a.get("heat") is not None else ""
            ie_b = ui.badge(f"🇮🇪 #{a['ireland_pos']} Ireland", "b-ie") if a.get("ireland_pos") else ""
            st.markdown(
                f"""<div class="card"><h4><span class="rank">{a['rank']:02d}</span>{esc(a['title'])} <span class="m">— {esc(a['artist'])}</span>
{ui.badge(a.get('momentum'))}{ui.badge(a['opp']['label'], a['opp']['cls'])}{ie_b}</h4>
<div class="row"><b>Trend:</b> {esc(a.get('trend') or '–')} · <b>Fits:</b> {esc(', '.join(a['cats']) or '—')}</div>
<div class="m">Heat {a.get('heat','–')}{delta} · Opportunity {a['opp']['score']} · Reels {fmt_num(a.get('reels'))} · {esc(a.get('also_charting') or '')}</div></div>""",
                unsafe_allow_html=True)
    elif view == "Ireland charts":
        chart = D.get("ireland_chart") or {}
        ui.section("Spotify weekly chart · Ireland",
                   f"Chart date {chart.get('chart_date','–')}. A regional proxy: what Ireland is streaming tends to show up in local Reels.")
        if ie:
            df = pd.DataFrame(ie).head(20)
            df["Song"] = df["artist"] + " — " + df["title"]
            irish = [x.lower() for x in TAGS.get("irish_artists", [])]
            df["Artist origin"] = df["artist"].str.lower().apply(lambda s: "Irish act" if any(x in s for x in irish) else "International")
            fig = px.bar(df, x="streams", y="Song", orientation="h", color="Artist origin",
                         color_discrete_map={"Irish act": GOLD, "International": NAVY}, labels={"streams": "Weekly streams", "Song": ""})
            fig.update_yaxes(categoryorder="total ascending")
            st.plotly_chart(ui.plotly_layout(fig, 580), width="stretch", config={"displayModeBar": False})
    else:
        ui.section("Best sounds for your business type")
        q = st.text_input("Filter by business type", placeholder="cafe, gym, salon, coach, tourism, school…")
        rows = [b for b in biz if not q or q.lower() in (b.get("best_for", "") + b.get("idea", "")).lower()]
        st.caption("⚠️ Most major-label songs may be unavailable on Business accounts. Check in-app before filming.")
        cols = st.columns(2)
        for i, b in enumerate(rows):
            with cols[i % 2]:
                st.markdown(
                    f"""<div class="card"><h4>{esc(b['title'])} <span class="m">— {esc(b['artist'])}</span>{ui.badge(b.get('stage'))}</h4>
<div class="m">{esc(b.get('mood',''))} · Reels {fmt_num(b.get('reels'))}</div>
<div class="row"><b>Best for:</b> {esc(b.get('best_for','–'))}</div>"""
                    + "".join(f'<div class="row">▸ {esc(x)}</div>' for x in (b.get("ideas") or [b.get("idea", "")])[:3] if x) + "</div>",
                    unsafe_allow_html=True)
        if not rows:
            st.info("No sounds match that filter.")

# --------------------------------------------------------------------------- #
# 4 · Hashtags
# --------------------------------------------------------------------------- #
with T[3]:
    hot, new = cat_ai.get("hashtags", []), cat_ai.get("new_hashtags", [])
    hc1, hc2 = st.columns([1.35, 1])
    with hc1:
        ui.section(f"{cat_cfg.get('icon','')} {category} hashtags", cat_ai.get("headline"))
        st.markdown('<span class="chip hot">AI pick this week</span><span class="chip new">New / seasonal</span><span class="chip">Curated</span>',
                    unsafe_allow_html=True)
        for tier, label in (("broad", "Broad reach · high competition"), ("mid", "Mid reach · best balance"),
                            ("niche", "Niche & local · most targeted")):
            st.markdown(f"<div class='small' style='margin-top:12px'>{label}</div>{ui.chips(cat_cfg.get(tier, []), hot)}", unsafe_allow_html=True)
        if new:
            st.markdown(f"<div class='small' style='margin-top:12px'>New this week</div>{ui.chips(new, new=new)}", unsafe_allow_html=True)
    with hc2:
        ui.section("Hashtag set builder", "A balanced mix, ready to paste. AI picks come first.")
        n_b = st.slider("Broad", 0, 5, 2)
        n_m = st.slider("Mid", 0, 8, 4)
        n_n = st.slider("Niche", 0, 9, 3)
        add_local = st.toggle("Add local tags", value=region != "Global")
        seasonal = st.toggle("Add seasonal tags", value=True)

        def tier_pick(tier, n):
            pool = cat_cfg[tier]
            return list(dict.fromkeys([t for t in hot if t in pool] + pool))[:n]

        pick = tier_pick("broad", n_b) + tier_pick("mid", n_m) + tier_pick("niche", n_n)
        if add_local:
            r = REGIONS["Ireland"] if region == "Ireland" else LOCAL
            pick += r["core"][:3] + (r.get("seasonal", [])[:2] if seasonal else [])
        elif seasonal:
            pick += new[:2]
        pick = list(dict.fromkeys(pick))
        st.code(" ".join(pick), language=None, wrap_lines=True)
        st.caption(f"{len(pick)} hashtags · 5–15 relevant tags usually beat 30 generic ones.")

    st.write("")
    ui.section("All categories at a glance", "This week's AI-picked hashtags per category.")
    grid = st.columns(3)
    for i, (c, cfg) in enumerate(CATS.items()):
        ai = AI_CATS.get(c, {})
        with grid[i % 3]:
            st.markdown(f'<div class="card"><h4>{cfg.get("icon","")} {esc(c)}</h4>'
                        f'{ui.chips((ai.get("hashtags") or cfg["mid"])[:6], hot=ai.get("hashtags"))}</div>', unsafe_allow_html=True)

# --------------------------------------------------------------------------- #
# 5 · Video examples
# --------------------------------------------------------------------------- #
with T[4]:
    REF = load_json(str(ROOT / "config" / "reference_reels.json"))
    ui.section(f"Sound & video examples · {category}",
               "Reels are grouped by SOUND: they show how creators use each trending audio (edit style, pacing, format), "
               "not necessarily your topic. Use them as format references, and use the hashtag links for topic inspiration.")
    vf = cat_ai.get("video_formats") or []
    v1, v2 = st.columns([1.2, 1])
    with v1:
        if vf:
            st.markdown('<div class="card soft"><b>Formats to film this week</b>' + "".join(f'<div class="row">▸ {esc(x)}</div>' for x in vf) + "</div>",
                        unsafe_allow_html=True)
    with v2:
        tags_for_links = list(dict.fromkeys((cat_ai.get("hashtags") or []) + cat_cfg["niche"][:3] + cat_cfg["mid"][:2]))[:6]
        st.markdown(f'<div class="card"><b>Topic inspiration on Instagram</b><div class="small">Real {esc(category)} posts, '
                    'opened in Instagram (you need to be logged in).</div></div>', unsafe_allow_html=True)
        lc = st.columns(2)
        for i, t in enumerate(tags_for_links):
            lc[i % 2].link_button(t, f"https://www.instagram.com/explore/tags/{t.lstrip('#')}/", width="stretch")

    own = [x.rstrip("/").split("/reel/")[-1].split("/")[0] for x in (REF.get(category) or []) if x]
    fit = [a for a in reels if category in a["cats"]]
    picks = [(a, c, "fit") for a in sorted(fit, key=lambda x: -x["opp"]["score"]) for c in (a.get("example_reels") or [])[:2]]
    if fit:
        st.markdown("**Sounds recommended for this category** · " + " · ".join(
            f"<b>{esc(a['title'])}</b> <span class='small'>({esc(a['why'].get(category, ''))})</span>" for a in fit), unsafe_allow_html=True)
    else:
        st.info(f"No trending sound this week is specifically recommended for {category}. Below are the week's top "
                "opportunity sounds as format references. For education, a talking-head tip over an instrumental or original audio is the safest choice.")
        picks = [(a, c, "general") for a in sorted(reels, key=lambda x: -x["opp"]["score"])[:6] for c in (a.get("example_reels") or [])[:1]]
    picks = [(None, c, "own") for c in own] + picks
    if picks:
        max_v = st.segmented_control("Examples to show", [3, 6, 9], default=3) or 3
        cols = st.columns(3)
        for i, (a, code, kind) in enumerate(picks[:max_v]):
            with cols[i % 3]:
                if kind == "own":
                    head = f'<b style="color:{NAVY}">Your reference</b> {ui.badge(category, "b-use")}'
                else:
                    head = (f'<b style="color:{NAVY}">{esc(a["title"])}</b> · {esc(a["artist"])} {ui.badge(a["opp"]["label"], a["opp"]["cls"])}'
                            + ("" if kind == "fit" else ui.badge("Format reference", "b-watch")))
                st.markdown(f'<div class="small" style="margin-bottom:6px">{head}</div>', unsafe_allow_html=True)
                components.html(
                    f'<iframe src="https://www.instagram.com/reel/{code}/embed/" width="100%" height="560" frameborder="0" scrolling="no" '
                    'allowtransparency="true" style="border:1px solid #e3e8ef;border-radius:12px;background:#fff"></iframe>', height=572)
                st.link_button("Open in Instagram ↗", f"https://www.instagram.com/reel/{code}/", width="stretch")
    st.caption("Tip: add your own topic-specific reference Reels per category in config/reference_reels.json and they appear first here.")

# --------------------------------------------------------------------------- #
# 6 · Script & Copy Studio
# --------------------------------------------------------------------------- #
with T[5]:
    ui.section("Script & Copy Studio",
               "Write your idea. Get hooks, a shot-by-shot script, a caption and hashtags built on this week's trends.")
    s1, s2 = st.columns([1, 1.35])
    with s1:
        with st.form("studio"):
            idea = st.text_area("Your idea", height=110,
                                placeholder="e.g. Open day at our school: show parents what a normal day looks like")
            f1, f2 = st.columns(2)
            fmt = f1.selectbox("Format", studio.FORMATS)
            length = f2.selectbox("Length", ["15 seconds", "30 seconds", "60 seconds", "5–7 slides", "3–5 stories"], index=1)
            f3, f4 = st.columns(2)
            goal = f3.selectbox("Goal", studio.GOALS, index=1)
            tone = f4.selectbox("Tone", studio.TONES, index=1)
            scat = st.selectbox("Category", list(CATS.keys()), index=list(CATS.keys()).index(category), key="scat")
            brand = st.text_input("Brand / account (optional)", placeholder="e.g. Limerick Christian School, Marketnus")
            local_on = st.toggle("Limerick local angle", value=region != "Global")
            go_btn = st.form_submit_button("✨ Generate", type="primary", width="stretch")
        if not has_key:
            st.caption("Template mode is on. Add `GEMINI_API_KEY` to Streamlit secrets for full AI scripts (free).")
    with s2:
        if go_btn and idea.strip():
            sai = AI_CATS.get(scat, {})
            s_aud = sorted([a for a in reels if scat in a["cats"]], key=lambda a: -a["opp"]["score"]) or reels[:3]
            ctx = {
                "audios": [{"title": a["title"], "artist": a["artist"], "trend": a.get("trend"), "status": a["opp"]["label"]} for a in s_aud[:5]],
                "tags": list(dict.fromkeys((sai.get("hashtags") or []) + (sai.get("new_hashtags") or []) + CATS[scat]["mid"][:4])),
                "local_tags": LOCAL["core"][:4] + LOCAL["seasonal"][:2],
                "slots": [ins.fmt_slot(s["dt"]) for s in slots],
            }
            brief = {"idea": idea.strip(), "category": scat, "fmt": fmt, "length": length, "goal": goal, "tone": tone,
                     "brand": brand or "not specified", "local": "Yes" if local_on else "No"}
            with st.spinner("Writing your script…"):
                try:
                    res = (studio.generate_ai(brief, ctx, secret("GEMINI_API_KEY"), secret("GEMINI_MODEL"))
                           if has_key else studio.generate_template(brief, ctx))
                except Exception as e:  # noqa: BLE001
                    st.warning(f"AI generation failed ({e.__class__.__name__}), so this was built with the template engine.")
                    res = studio.generate_template(brief, ctx)
            st.session_state["studio_result"] = res
        elif go_btn:
            st.warning("Write your idea first.")

        res = st.session_state.get("studio_result")
        if res:
            st.markdown(f'<div class="card navy"><h4>{esc(res.get("title",""))}</h4>'
                        f'<div class="small" style="color:{GOLD}">{esc(res.get("_engine",""))}</div></div>', unsafe_allow_html=True)
            st.markdown("**Hook options**")
            for h in res.get("hooks", []):
                st.markdown(f"- {h}")
            if res.get("script"):
                st.markdown("**Script**")
                st.dataframe(pd.DataFrame(res["script"]).rename(columns={"time": "Time", "visual": "Visual", "voiceover": "Voiceover",
                                                                         "on_screen_text": "On-screen text"}), hide_index=True, width="stretch")
            if res.get("slides"):
                st.markdown("**Carousel slides**")
                st.dataframe(pd.DataFrame(res["slides"]).rename(columns={"slide": "#", "headline": "Headline", "body": "Body"}),
                             hide_index=True, width="stretch")
            st.markdown("**Caption**")
            st.code(f"{res.get('caption','')}\n\n{' '.join(res.get('hashtags', []))}", language=None, wrap_lines=True)
            if res.get("alt_captions"):
                with st.expander("Alternative captions"):
                    for c in res["alt_captions"]:
                        st.code(c, language=None, wrap_lines=True)
            au = res.get("audio", {})
            st.markdown(f'<div class="card soft"><div class="row"><b>🎵 Audio:</b> {esc(au.get("pick",""))}. {esc(au.get("why",""))}</div>'
                        f'<div class="row"><b>Business-safe option:</b> {esc(au.get("business_safe_alternative",""))}</div>'
                        f'<div class="row"><b>🕒 Best time:</b> {esc(res.get("best_time",""))}</div>'
                        + "".join(f'<div class="row">▸ {esc(t)}</div>' for t in res.get("production_tips", [])) + "</div>",
                        unsafe_allow_html=True)
            st.download_button("Download script (.txt)", studio.as_text(res).encode(), "instagram-script.txt", width="stretch")
        else:
            st.markdown('<div class="card soft"><b>How it works</b><div class="row">1. Describe your idea in one or two lines.</div>'
                        '<div class="row">2. Pick a format, goal and tone.</div><div class="row">3. Get hooks, a script, a caption, hashtags, '
                        "audio and the best time to post, all based on this week's data.</div></div>", unsafe_allow_html=True)

    st.write("")
    ui.section("Caption checker", "Paste any caption to score it before you post.")
    cc1, cc2 = st.columns([1.35, 1])
    with cc1:
        cap = st.text_area("Caption", height=190, placeholder="Paste your caption with hashtags…", label_visibility="collapsed")
    with cc2:
        if cap.strip():
            r = studio.check_caption(cap, LOCAL["core"] + LOCAL["nearby"] + LOCAL["seasonal"] + REGIONS["Ireland"]["core"])
            col = NAVY if r["score"] >= 75 else GOLD if r["score"] >= 50 else BURGUNDY_2
            st.markdown(f'<div class="score" style="border:8px solid {col}">{r["score"]}</div>'
                        f'<div class="small" style="text-align:center">{r["words"]} words · {r["hashtags"]} hashtags · {r["emojis"]} emojis</div>',
                        unsafe_allow_html=True)
            st.markdown("".join(f'<div class="check">{"✅" if ok else "⬜"} {esc(lbl)}</div>' for lbl, ok, _ in r["checks"]),
                        unsafe_allow_html=True)
        else:
            st.markdown('<div class="card soft small">Your score appears here, checking the hook, CTA, length, hashtag mix, local tags and readability.</div>',
                        unsafe_allow_html=True)

# --------------------------------------------------------------------------- #
# 7 · Limerick local
# --------------------------------------------------------------------------- #
with T[6]:
    L = A.get("limerick_local", {})
    ui.section("Limerick + 50 km", " · ".join(LOCAL["towns"]))
    if L.get("headline"):
        st.markdown(f'<div class="card navy"><b>This week locally</b><div class="row">{esc(L["headline"])}</div></div>', unsafe_allow_html=True)
    l1, l2 = st.columns(2)
    with l1:
        st.markdown("**Content ideas**")
        for t in L.get("ideas", []):
            st.markdown(f"- {t}")
        st.markdown("**Local hashtags**")
        for lbl, key in (("Core", "core"), ("Nearby towns", "nearby"), ("Seasonal", "seasonal")):
            st.markdown(f"<div class='small' style='margin-top:8px'>{lbl}</div>" + ui.chips(LOCAL[key], hot=L.get("hashtags", [])),
                        unsafe_allow_html=True)
    with l2:
        st.markdown("**Ready-to-use local copies**")
        for cp in L.get("sample_copies", []):
            st.code(cp + "\n\n" + " ".join(L.get("hashtags", [])[:6]), language=None, wrap_lines=True)
        irish = [x.lower() for x in TAGS.get("irish_artists", [])]
        ia = [i for i in ie[:20] if any(x in i["artist"].lower() for x in irish)]
        if ia:
            st.markdown("**Irish acts in the national top 20**")
            st.dataframe(pd.DataFrame(ia)[["pos", "artist", "title", "change"]]
                         .rename(columns={"pos": "#", "artist": "Artist", "title": "Title", "change": "Move"}),
                         hide_index=True, width="stretch")

# --------------------------------------------------------------------------- #
# 8 · Sources
# --------------------------------------------------------------------------- #
with T[7]:
    ui.section("Sources & data status")
    for s in [D.get("reels_audio"), D.get("business_audio"), D.get("ireland_chart")]:
        if s:
            st.markdown(f"- **[{s['source']}]({s['url']})** · fetched {s.get('fetched_at','')[:10]}")
    st.markdown(f"- **[Posting times: Buffer 2026]({INS['posting_times']['url']})**: {INS['posting_times']['source']}")
    st.markdown("- **Hashtag sets:** curated in `config/hashtags.json` · **Key dates & category keywords:** `config/insights.json`")
    st.markdown(f"- **AI analysis:** {A.get('_meta',{}).get('model','–')}")
    st.json(D.get("source_status", {}), expanded=False)
    st.caption("Heat scores and reel counts come from the sources at publish time and are approximate. Spotify Ireland is a regional "
               "proxy, not Instagram data. The Opportunity score is this dashboard's own metric (Heat adjusted for saturation).")

st.markdown(f'<div class="small" style="text-align:center;margin-top:40px;padding-top:14px;border-top:1px solid rgba(11,55,103,.12)">'
            f'<b style="color:{NAVY}">{APP_NAME}</b> · Developed by <b>{DEVELOPER}</b> · Data refreshes every Friday</div>',
            unsafe_allow_html=True)
