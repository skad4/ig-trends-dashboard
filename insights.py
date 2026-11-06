"""Derived insights: opportunity score, posting heatmap, next slots, weekly plan."""
from __future__ import annotations

import math
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd

TZ = ZoneInfo("Europe/Dublin")
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
TIER_W = {"Highest": 1.0, "High": 0.85, "Moderate": 0.7, "Low": 0.55}


# --------------------------------------------------------------------------- #
# Audio opportunity
# --------------------------------------------------------------------------- #
def opportunity(a: dict) -> dict:
    """Score = heat penalised by saturation (number of reels already using it)."""
    heat = a.get("heat") or 0
    reels = a.get("reels")
    sat = 0.35 if not reels else min(max(math.log10(reels) - 4, 0) / (math.log10(6e6) - 4), 1)
    score = round(heat * (1 - 0.45 * sat))
    if reels and reels >= 1_000_000:
        label, cls = "Saturated", "b-sat"
    elif heat >= 55 and sat < 0.55:
        label, cls = "Use now", "b-use"
    elif heat >= 55:
        label, cls = "Ride the wave", "b-ride"
    else:
        label, cls = "Early · watch", "b-watch"
    return {"score": score, "saturation": round(sat, 2), "label": label, "cls": cls}


def audio_categories(a: dict, biz_by_title: dict, ai_cats: dict, keywords: dict) -> list[str]:
    title = a.get("title", "").lower()
    text = " ".join([a.get("trend", ""), biz_by_title.get(title, {}).get("best_for", ""),
                     biz_by_title.get(title, {}).get("idea", "")]).lower()
    cats = {c for c, v in ai_cats.items() if title and title in (v.get("suggested_audio") or "").lower()}
    for c, kws in keywords.items():
        if any(k in text for k in kws):
            cats.add(c)
    return sorted(cats)


# --------------------------------------------------------------------------- #
# Posting times
# --------------------------------------------------------------------------- #
def heat_grid(cfg: dict) -> pd.DataFrame:
    hours = list(range(6, 24))
    rows = []
    for d in DAYS:
        info = cfg["days"][d]
        w = TIER_W.get(info["tier"], 0.6)
        for h in hours:
            if h in info["slots"]:
                v = w * (1.0 - 0.12 * info["slots"].index(h))
            elif 18 <= h <= 23:
                v = w * 0.55
            elif 12 <= h <= 17:
                v = w * 0.42
            else:
                v = w * 0.30
            rows.append({"day": d[:3], "hour": h, "score": round(v * 100)})
    return pd.DataFrame(rows)


def next_slots(cfg: dict, n: int = 3, now: datetime | None = None) -> list[dict]:
    now = now or datetime.now(TZ)
    out = []
    for offset in range(0, 8):
        day = (now + timedelta(days=offset)).date()
        name = DAYS[day.weekday()]
        info = cfg["days"][name]
        for rank, h in enumerate(info["slots"]):
            dt = datetime(day.year, day.month, day.day, h, tzinfo=TZ)
            if dt > now:
                out.append({"dt": dt, "day": name, "tier": info["tier"], "rank": rank + 1,
                            "w": TIER_W.get(info["tier"], .6) * (1 - .12 * rank)})
    out.sort(key=lambda x: (-x["w"], x["dt"]))
    best = sorted(out[: max(n * 2, 6)], key=lambda x: x["dt"])
    top = sorted(out, key=lambda x: -x["w"])[:n]
    return sorted(top, key=lambda x: x["dt"]) if top else best[:n]


def fmt_slot(dt: datetime) -> str:
    return dt.strftime("%a %d %b · %H:%M").replace(" 0", " ")


def upcoming_dates(dates: list[dict], category: str | None, today: date | None = None, n: int = 6) -> list[dict]:
    today = today or datetime.now(TZ).date()
    out = []
    for d in dates:
        dd = date.fromisoformat(d["date"])
        if dd < today:
            continue
        if category and category != "All" and "All" not in d["tags"] and category not in d["tags"]:
            continue
        out.append({**d, "days": (dd - today).days, "d": dd})
    return sorted(out, key=lambda x: x["d"])[:n]


# --------------------------------------------------------------------------- #
# Weekly plan
# --------------------------------------------------------------------------- #
def weekly_plan(category: str, ai_cat: dict, cat_tags: dict, audios: list[dict], cfg_times: dict,
                local_tags: list[str]) -> pd.DataFrame:
    today = datetime.now(TZ).date()
    formats = (ai_cat.get("video_formats") or []) + [ai_cat.get("content_idea", "")]
    formats = [f for f in formats if f] or ["Reel: quick tip", "Carousel: how-to", "Story: poll"]
    plan_set = {"Monday", "Tuesday", "Wednesday", "Thursday", "Sunday"}  # skip weak Fri/Sat
    days = [today + timedelta(days=k) for k in range(1, 8)]
    days = [d for d in days if DAYS[d.weekday()] in plan_set]
    tags = ai_cat.get("hashtags") or (cat_tags.get("broad", [])[:2] + cat_tags.get("mid", [])[:3] + cat_tags.get("niche", [])[:2])
    rows = []
    for i, d in enumerate(days):
        slot = cfg_times["days"][DAYS[d.weekday()]]["slots"][0]
        a = audios[i % len(audios)] if audios else {}
        rows.append({
            "Date": d.strftime("%a %d %b"),
            "Time": f"{slot:02d}:00",
            "Format": formats[i % len(formats)],
            "Audio": f"{a.get('title','Original audio')} — {a.get('artist','')}".strip(" —"),
            "Hashtags": " ".join(list(dict.fromkeys(tags[:6] + local_tags[:2]))),
        })
    return pd.DataFrame(rows)
