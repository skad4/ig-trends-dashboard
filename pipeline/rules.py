"""Rule-based weekly analysis: no API key needed.

Builds the same JSON shape as the Gemini analysis, from this week's data only,
so the dashboard's insights refresh every week even without AI.
"""
from __future__ import annotations

import json
import math
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CTA = {
    "Education": "Places are limited. Enrol via the link in bio 🎓",
    "Business & Marketing": "Want the same plan? DM us 'PLAN'.",
    "Tech & AI": "Comment 'AI' and we'll send you the workflow.",
    "Local Business": "Pop in this week or comment GIFT for the full list 🎁",
    "Food & Drink": "Book your table. Link in bio.",
    "Fitness & Wellness": "Free trial week. Link in bio 💪",
    "Beauty": "Limited slots, so book now via the link in bio 💅",
    "Travel & Tourism": "Save this for your next weekend escape.",
    "Fashion": "Which look: 1, 2 or 3? All available in-store.",
}
FORMAT_HINTS = {
    "Education": ["Reel: talking-head tip with on-screen text over an instrumental (15–20s)",
                  "Carousel: '5 things to learn this month' with a save CTA on the last slide",
                  "Story: poll — 'What do you want to learn next?'"],
    "Business & Marketing": ["Reel: before/after results montage", "Carousel: step-by-step checklist in 6 slides"],
    "Tech & AI": ["Reel: 'before vs after' screen recording reveal", "Carousel: 5 tools with one-line use cases"],
    "Local Business": ["Reel: product/window reveal in 5 quick cuts", "Story: countdown sticker to your next offer"],
    "Food & Drink": ["Reel: menu items, one per beat", "Carousel: 'Where to eat in Limerick this month'"],
    "Fitness & Wellness": ["Reel: Day 1 vs Day 100 member story", "Reel: short workout with a timer on screen"],
    "Beauty": ["Reel: menu of looks, one design per beat", "Reel: get-ready-with-me"],
    "Travel & Tourism": ["Reel: slow cinematic landscape reveal", "Carousel: weekend itinerary from Limerick"],
    "Fashion": ["Reel: 3 outfits on the beat", "Carousel: one piece styled three ways"],
}


def _sat(reels):
    return 0.35 if not reels else min(max(math.log10(reels) - 4, 0) / (math.log10(6e6) - 4), 1)


def _score(a):
    return round((a.get("heat") or 0) * (1 - 0.45 * _sat(a.get("reels"))))


def _cats_for(a, biz_by_title, keywords):
    text = " ".join([a.get("trend", ""), biz_by_title.get(a["title"].lower(), {}).get("best_for", ""),
                     biz_by_title.get(a["title"].lower(), {}).get("idea", "")]).lower()
    return {c for c, kws in keywords.items() if any(k in text for k in kws)}


def run_rules(reels: list, biz: list, ie: list, tags_cfg: dict, ins_cfg: dict, today: date | None = None) -> dict:
    today = today or datetime.now(timezone.utc).date()
    cats = tags_cfg["categories"]
    local = tags_cfg["regions"]["Limerick +50km"]
    biz_by_title = {b["title"].lower(): b for b in biz}
    kw = ins_cfg.get("audio_category_keywords", {})
    ranked = sorted(reels, key=_score, reverse=True)
    rising = [a for a in reels if "ris" in (a.get("momentum") or "").lower()]
    returning = [a for a in reels if "return" in (a.get("momentum") or "").lower()]
    saturated = [a for a in reels if (a.get("reels") or 0) >= 1_000_000]
    cross = [a for a in reels if a.get("ireland_pos")]
    top = reels[0] if reels else {}
    irish_names = [x.lower() for x in tags_cfg.get("irish_artists", [])]
    irish_ie = [i for i in ie[:20] if any(x in i["artist"].lower() for x in irish_names)]
    upcoming = [d for d in ins_cfg.get("key_dates", []) if date.fromisoformat(d["date"]) >= today][:3]
    seasonal_on = any((date.fromisoformat(d["date"]) - today).days <= 45 and "christmas" in d["name"].lower()
                      for d in ins_cfg.get("key_dates", []) if date.fromisoformat(d["date"]) >= today)

    # summary ----------------------------------------------------------------
    parts = []
    if top:
        parts.append(f"'{top['title']}' by {top['artist']} leads Instagram Reels this week (Heat {top.get('heat')}).")
    if returning:
        parts.append(f"{len(returning)} seasonal or returning sounds are back ({', '.join(a['title'] for a in returning[:3])}).")
    if ranked:
        parts.append(f"The best opportunity right now is '{ranked[0]['title']}': high heat and not yet crowded.")
    summary = " ".join(parts) or "No trend data this week."

    takeaways = []
    if cross:
        takeaways.append("Reels × Ireland crossover: " + ", ".join(f"'{a['title']}' (#{a['ireland_pos']} in Ireland)" for a in cross[:3])
                         + ". These are the strongest local signals.")
    if rising:
        takeaways.append(f"{len(rising)} of {len(reels)} tracked sounds are rising: move early on "
                         + ", ".join(f"'{a['title']}'" for a in rising[:3]) + ".")
    if saturated:
        takeaways.append(", ".join(f"'{a['title']}'" for a in saturated) + " already has 1M+ reels, so you need a strong hook to stand out.")
    takeaways.append("Most major-label songs may be blocked for Business accounts: reuse the same formats with original audio or a voiceover.")

    ireland_signal = ""
    if cross or irish_ie:
        bits = []
        if cross:
            bits.append("Also charting in Ireland: " + ", ".join(f"{a['title']} (#{a['ireland_pos']})" for a in cross[:3]) + ".")
        if irish_ie:
            names = list(dict.fromkeys(i["artist"] for i in irish_ie))
            bits.append(f"Irish acts in the top 20: {', '.join(names[:4])}. Good material for Irish-pride content.")
        ireland_signal = " ".join(bits)

    audio_picks = []
    for a in ranked[:5]:
        b = biz_by_title.get(a["title"].lower(), {})
        audio_picks.append({
            "title": a["title"], "artist": a["artist"],
            "why_now": f"Heat {a.get('heat')}, {(a.get('momentum') or '').lower()}"
                       + (f", #{a['ireland_pos']} in Ireland" if a.get("ireland_pos") else ""),
            "best_for": b.get("best_for") or a.get("trend", ""),
            "business_account_tip": "If it's unavailable on a Business account, copy the format "
                                    f"('{a.get('trend','')}') with a library track or voiceover.",
        })

    # categories -------------------------------------------------------------
    out_cats = {}
    for c, cfg in cats.items():
        fits = [a for a in ranked if c in _cats_for(a, biz_by_title, kw)]
        a0 = fits[0] if fits else (ranked[0] if ranked else {})
        wk = today.isocalendar()[1]  # rotate picks weekly so sets stay fresh
        rot = lambda lst, n: [lst[(wk + i) % len(lst)] for i in range(min(n, len(lst)))] if lst else []  # noqa: E731
        hashtags = cfg["broad"][:1] + rot(cfg["mid"], 3) + rot(cfg["niche"], 3)
        new = [t for t in local.get("seasonal", [])[:1]] if seasonal_on and c in ("Local Business", "Food & Drink", "Beauty", "Fashion") else []
        trend = a0.get("trend", "trending format")
        out_cats[c] = {
            "headline": f"'{trend}' is the format to borrow this week"
                        + (f", led by '{a0['title']}'." if a0 else "."),
            "content_idea": f"Adapt the '{trend}' format to {c.lower()}: one clear message, a hook in the first second and a clear call to action at the end.",
            "suggested_audio": f"{a0.get('title','Original audio')} — {a0.get('artist','')}".strip(" —"),
            "video_formats": FORMAT_HINTS.get(c, []),
            "hashtags": hashtags,
            "new_hashtags": new,
            "sample_copies": [
                f"This week's trend, our way ✨ {CTA[c]}",
                f"Save this for later 👇 3 quick tips on {c.lower()} you can use today.",
            ],
        }

    limerick = {
        "headline": ("Seasonal and local content wins this week: " + upcoming[0]["name"] + f" is in {(date.fromisoformat(upcoming[0]['date']) - today).days} days.")
                    if upcoming else "Local faces and places drive the most engagement.",
        "ideas": [
            "A 'best of Limerick' Reel: 5 local spots in 15 seconds, made as a Collab post with a neighbouring business.",
            "Behind-the-scenes with a real local face: your team, a customer or a student.",
            "Ask customers to tag #lovelimerick and your handle for a monthly giveaway.",
        ],
        "hashtags": local["core"][:4] + local["nearby"][:2] + (local["seasonal"][:1] if seasonal_on else []),
        "sample_copies": [
            "Limerick, this one's for you 💙 Tag someone you'd bring!",
            "5 spots in Limerick you need to visit this month ✨ Save + share with your crew.",
        ],
    }

    return {
        "week_summary": summary,
        "key_takeaways": takeaways,
        "ireland_signal": ireland_signal,
        "audio_picks": audio_picks,
        "categories": out_cats,
        "limerick_local": limerick,
        "opportunities": [f"{d['name']} ({d['date']}): plan content now." for d in upcoming]
                         + ([f"Early movers: {', '.join(a['title'] for a in rising[:3])}."] if rising else []),
        "watch_out": ([f"Saturated sounds: {', '.join(a['title'] for a in saturated)}."] if saturated else [])
                     + ["Check audio availability on Business accounts before filming."],
        "_meta": {"model": "Rule-based engine (no AI key)", "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                  "kind": "rules"},
    }


if __name__ == "__main__":
    d = json.loads((ROOT / "data" / "latest.json").read_text())
    tags = json.loads((ROOT / "config" / "hashtags.json").read_text())
    ins = json.loads((ROOT / "config" / "insights.json").read_text())
    r = run_rules(d["reels_audio"]["items"], d["business_audio"]["items"], d["ireland_chart"]["items"], tags, ins)
    print(json.dumps({k: r[k] for k in ("week_summary", "key_takeaways", "ireland_signal")}, indent=2, ensure_ascii=False))
    print(json.dumps(r["categories"]["Education"], indent=2, ensure_ascii=False))
