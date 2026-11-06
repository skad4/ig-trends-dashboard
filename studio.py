"""Script & Copy Studio — idea in, ready-to-post script/caption out.
Uses Gemini when a key is available (Streamlit secrets or env), otherwise a
template engine built on this week's data so the tool always works."""
from __future__ import annotations

import json
import re

from pipeline.gemini import call_gemini

FORMATS = ["Reel script", "Carousel", "Single post caption", "Story sequence"]
GOALS = ["Awareness / reach", "Engagement (saves & shares)", "Leads / bookings", "Enrolments / sign-ups", "Sales / offer"]
TONES = ["Professional", "Friendly", "Inspirational", "Playful", "Bold & direct"]

STUDIO_PROMPT = """You are an expert Instagram content strategist and scriptwriter for small
businesses and education brands in Limerick, Ireland. Write in English (Irish/UK spelling).

BRIEF
- Idea: {idea}
- Category: {category}
- Format: {fmt} ({length})
- Goal: {goal}
- Tone: {tone}
- Brand / account: {brand}
- Local angle (Limerick + 50 km): {local}

THIS WEEK'S DATA (use it, do not invent stats)
- Trending audio: {audios}
- Recommended hashtags for the category: {tags}
- Local hashtags: {local_tags}
- Best upcoming posting slots: {slots}

Rules: hook must land in the first 1.5 seconds / first 125 characters; caption max 2,200
chars but aim for 80–220 words before hashtags; 5–12 hashtags mixing broad/mid/niche;
note that major-label songs may be unavailable for Business accounts and give an alternative.

Return ONLY JSON:
{{
  "title": "short working title",
  "hooks": ["3 alternative hooks"],
  "script": [{{"time": "0–3s", "visual": "", "voiceover": "", "on_screen_text": ""}}],
  "slides": [{{"slide": 1, "headline": "", "body": ""}}],
  "caption": "full caption with line breaks and emojis where natural",
  "alt_captions": ["2 shorter alternatives"],
  "cta": "",
  "hashtags": ["#..."],
  "audio": {{"pick": "title — artist", "why": "", "business_safe_alternative": ""}},
  "best_time": "",
  "production_tips": ["3 quick filming/design tips"]
}}
Use "script" for Reels/Stories and "slides" for Carousels (empty list for the other)."""


def generate_ai(brief: dict, ctx: dict, api_key: str, model: str | None = None) -> dict:
    prompt = STUDIO_PROMPT.format(**brief, **{k: json.dumps(v, ensure_ascii=False) for k, v in ctx.items()})
    out = call_gemini(prompt, api_key=api_key, model=model, temperature=0.85, timeout=90)
    out["_engine"] = "Gemini"
    return out


def _sentence(s: str) -> str:
    s = s.strip().rstrip(".")
    return s[:1].upper() + s[1:] if s else s


def generate_template(brief: dict, ctx: dict) -> dict:
    idea = _sentence(brief["idea"]) or "Your idea"
    goal_cta = {
        "Awareness / reach": "Follow for more and share this with someone who needs it.",
        "Engagement (saves & shares)": "Save this for later and tag a friend 👇",
        "Leads / bookings": "Book your spot. Link in bio or DM us 'INFO'.",
        "Enrolments / sign-ups": "Places are limited. Enrol via the link in bio 🎓",
        "Sales / offer": "Shop now. Offer ends soon. Link in bio.",
    }[brief["goal"]]
    local = " in Limerick" if brief["local"] == "Yes" else ""
    audios = ctx.get("audios") or []
    a0 = audios[0] if audios else {"title": "Original audio", "artist": ""}
    hooks = [
        f"Nobody talks about this{local}: {idea.lower()}",
        f"3 things I wish I knew about {idea.lower()} 👇",
        f"Stop scrolling if you care about {idea.lower()}",
    ]
    script = [
        {"time": "0–2s", "visual": "Close-up, fast movement or a bold text card", "voiceover": hooks[0], "on_screen_text": hooks[0]},
        {"time": "2–8s", "visual": "Show the problem or the 'before'", "voiceover": f"Here's what usually happens with {idea.lower()}…", "on_screen_text": "The problem"},
        {"time": "8–20s", "visual": "3 quick cuts: tip 1, tip 2, tip 3", "voiceover": "Here's how to fix it, step by step.", "on_screen_text": "1 · 2 · 3"},
        {"time": "20–25s", "visual": "Result / 'after' shot, smiling face or the final product", "voiceover": "And that's the result.", "on_screen_text": "The result ✨"},
        {"time": "25–30s", "visual": "Logo + CTA card", "voiceover": goal_cta, "on_screen_text": goal_cta},
    ]
    slides = [
        {"slide": 1, "headline": hooks[1], "body": "Swipe →"},
        {"slide": 2, "headline": "The problem", "body": f"Why {idea.lower()} feels harder than it should."},
        {"slide": 3, "headline": "Step 1", "body": "Start small and make it specific."},
        {"slide": 4, "headline": "Step 2", "body": "Show, don't tell: use a real example."},
        {"slide": 5, "headline": "Step 3", "body": "Repeat weekly and track what works."},
        {"slide": 6, "headline": "Your turn", "body": goal_cta},
    ]
    caption = (f"{hooks[0]} 👀\n\n{idea}{local} doesn't have to be complicated. Here's the simple version:\n\n"
               f"✅ Start with one clear step\n✅ Show a real example\n✅ Stay consistent\n\n{goal_cta}")
    fmt = brief["fmt"]
    return {
        "title": idea[:60],
        "hooks": hooks,
        "script": script if fmt in ("Reel script", "Story sequence") else [],
        "slides": slides if fmt == "Carousel" else [],
        "caption": caption,
        "alt_captions": [f"{idea}{local}, made simple. {goal_cta}", f"Save this: {idea.lower()} in 3 steps 👇"],
        "cta": goal_cta,
        "hashtags": list(dict.fromkeys((ctx.get("tags") or [])[:8] + ((ctx.get("local_tags") or [])[:3] if brief["local"] == "Yes" else [])))[:12],
        "audio": {"pick": f"{a0.get('title')} — {a0.get('artist')}", "why": "Top trending sound this week.",
                  "business_safe_alternative": "If it's unavailable on a Business account, use a similar track from the Reels audio library or a voiceover over an instrumental."},
        "best_time": (ctx.get("slots") or ["Wed 12:00"])[0],
        "production_tips": ["Film vertical 9:16 in natural light", "Add captions: most people watch muted",
                            "Keep the first frame bold. It's also your cover"],
        "_engine": "Template (add GEMINI_API_KEY for AI generation)",
    }


def as_text(r: dict) -> str:
    lines = [f"# {r.get('title','')}", "", "HOOKS"] + [f"- {h}" for h in r.get("hooks", [])]
    if r.get("script"):
        lines += ["", "SCRIPT"] + [f"[{s.get('time')}] VISUAL: {s.get('visual')} | VO: {s.get('voiceover')} | TEXT: {s.get('on_screen_text')}" for s in r["script"]]
    if r.get("slides"):
        lines += ["", "SLIDES"] + [f"{s.get('slide')}. {s.get('headline')}: {s.get('body')}" for s in r["slides"]]
    lines += ["", "CAPTION", r.get("caption", ""), "", " ".join(r.get("hashtags", [])),
              "", f"AUDIO: {r.get('audio',{}).get('pick','')}", f"BEST TIME: {r.get('best_time','')}"]
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Caption checker
# --------------------------------------------------------------------------- #
CTA_WORDS = ["link in bio", "dm", "book", "comment", "save", "share", "tag", "follow", "enrol", "enroll",
             "sign up", "register", "shop", "visit", "call", "click", "join", "apply"]


def check_caption(text: str, local_tags: list[str]) -> dict:
    t = text or ""
    tags = re.findall(r"#\w+", t)
    body = re.sub(r"#\w+", "", t).strip()
    first = body.split("\n")[0][:125]
    words = len(body.split())
    emojis = len(re.findall(r"[\U0001F300-\U0001FAFF☀-➿]", t))
    checks = [
        ("Hook in the first line (≤125 characters)", 0 < len(first) <= 125 and len(body.split("\n")[0]) <= 125, 15),
        ("Clear call to action", any(w in body.lower() for w in CTA_WORDS), 20),
        ("Length 30–220 words", 30 <= words <= 220, 15),
        ("5–15 hashtags", 5 <= len(tags) <= 15, 15),
        ("Includes a local Limerick/Ireland tag", any(x.lower() in [l.lower() for l in local_tags] for x in tags), 10),
        ("Uses line breaks for readability", body.count("\n") >= 2, 10),
        ("1–6 emojis (not overloaded)", 1 <= emojis <= 6, 5),
        ("No repeated hashtags", len(tags) == len({x.lower() for x in tags}), 10),
    ]
    score = sum(w for _, ok, w in checks if ok)
    return {"score": score, "checks": checks, "words": words, "hashtags": len(tags), "emojis": emojis}
