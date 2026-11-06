"""Weekly AI analysis with Google Gemini (free tier).

Needs the env var GEMINI_API_KEY (get one free at https://aistudio.google.com/apikey).
Optional: GEMINI_MODEL (default gemini-2.5-flash).
If the key is missing or the call fails, returns None and the previous analysis is kept.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from pipeline.gemini import call_gemini

PROMPT = """You are a senior social media strategist for small businesses and education
brands in Limerick, Ireland (market: Limerick city + 50 km radius: Ennis, Shannon,
Nenagh, Adare, Killaloe, Newcastle West...). Analyse this week's Instagram trend data and
write a practical briefing in English.

Rules:
- Only rely on the data provided. Do not invent reel counts, chart positions or stats.
- Note that most major-label songs may be unavailable for Business accounts; when relevant,
  suggest an alternative (original audio, voiceover, Reels-only/library sounds).
- Hashtags: choose 5-8 per category from the curated sets given (you may add at most 2
  timely/seasonal ones, flagged in "new_hashtags"). Mix broad + mid + niche.
- Copies: short (max 220 characters before hashtags), punchy, with a clear CTA.
- Compare with last week's data if provided.

Return ONLY valid JSON with this exact shape:
{
  "week_summary": "2-3 sentences",
  "key_takeaways": ["...", "...", "..."],
  "ireland_signal": "1-2 sentences on which Reels sounds are also hot in Ireland",
  "audio_picks": [
    {"title": "", "artist": "", "why_now": "", "best_for": "", "business_account_tip": ""}
  ],
  "categories": {
    "<category name>": {
      "headline": "", "content_idea": "", "suggested_audio": "",
      "video_formats": ["format 1 (Reel/Carousel/Story + what to film)", "format 2"],
      "hashtags": ["#..."], "new_hashtags": ["#..."],
      "sample_copies": ["...", "..."]
    }
  },
  "limerick_local": {
    "headline": "", "ideas": ["...", "..."], "hashtags": ["#..."],
    "sample_copies": ["...", "..."]
  },
  "opportunities": ["..."],
  "watch_out": ["..."]
}
Include every category listed in the data.

DATA:
"""


def run_analysis(payload: dict, previous: dict | None = None) -> dict | None:
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        print("[analyze] GEMINI_API_KEY not set — keeping previous analysis")
        return None
    model = os.getenv("GEMINI_MODEL") or "gemini-2.5-flash"

    data = {"this_week": payload}
    if previous:
        data["last_week"] = {
            "reels_audio": [
                {k: a.get(k) for k in ("rank", "title", "artist", "heat")}
                for a in (previous.get("reels_audio") or {}).get("items", [])
            ],
        }

    try:
        result = call_gemini(PROMPT + json.dumps(data, ensure_ascii=False), api_key=key,
                             model=model, temperature=0.6)
    except Exception as e:  # noqa: BLE001
        print(f"[analyze] Gemini call failed: {e}")
        return None

    result["_meta"] = {
        "model": model,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "kind": "ai",
    }
    return result
