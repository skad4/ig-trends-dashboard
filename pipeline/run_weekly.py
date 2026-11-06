"""Weekly pipeline: collect -> cross-reference -> AI analysis -> save.

Run locally:   python -m pipeline.run_weekly
Run in CI:     see .github/workflows/weekly-update.yml
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from pipeline.analyze import run_analysis
from pipeline.rules import run_rules
from pipeline import ig_profiles, ig_insights
from pipeline.collect import (
    collect_creatordb,
    collect_kworb_ie,
    collect_socialpilot,
    cross_reference,
)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
LATEST = DATA / "latest.json"
HISTORY = DATA / "history"
HASHTAGS = ROOT / "config" / "hashtags.json"


def load(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None


def main() -> None:
    DATA.mkdir(exist_ok=True)
    HISTORY.mkdir(exist_ok=True)
    prev = load(LATEST) or {}
    tags = load(HASHTAGS) or {}

    creatordb = collect_creatordb()
    socialpilot = collect_socialpilot()
    kworb = collect_kworb_ie()

    # keep last good copy of anything that failed
    status = {}
    for name, new, key in (
        ("CreatorDB", creatordb, "reels_audio"),
        ("SocialPilot", socialpilot, "business_audio"),
        ("Kworb Ireland", kworb, "ireland_chart"),
    ):
        status[name] = "updated" if new else "kept previous (fetch/parse failed)"
    creatordb = creatordb or prev.get("reels_audio")
    socialpilot = socialpilot or prev.get("business_audio")
    kworb = kworb or prev.get("ireland_chart")
    cross_reference(creatordb, kworb)

    now = datetime.now(timezone.utc)
    out = {
        "updated_at": now.isoformat(timespec="seconds"),
        "week": now.strftime("%G-W%V"),
        "source_status": status,
        "reels_audio": creatordb,
        "business_audio": socialpilot,
        "ireland_chart": kworb,
    }

    ai_input = {
        "reels_audio_global": (creatordb or {}).get("items", []),
        "business_use_notes": (socialpilot or {}).get("items", []),
        "ireland_spotify_top20": (kworb or {}).get("items", [])[:20],
        "curated_hashtags": tags.get("categories", {}),
        "limerick_region": tags.get("regions", {}).get("Limerick +50km", {}),
        "today": now.date().isoformat(),
    }
    analysis = run_analysis(ai_input, previous=prev)
    if analysis:
        status["Analysis"] = "updated (Gemini)"
    else:
        try:
            ins_cfg = load(ROOT / "config" / "insights.json") or {}
            analysis = run_rules((creatordb or {}).get("items", []), (socialpilot or {}).get("items", []),
                                 (kworb or {}).get("items", []), tags, ins_cfg)
            status["Analysis"] = "updated (rule-based, no AI key)"
        except Exception as e:  # noqa: BLE001
            print(f"[rules] failed: {e}")
            analysis = prev.get("analysis")
            status["Analysis"] = "kept previous"
    out["analysis"] = analysis

    # Instagram: public profile numbers for every school (no login) + optional LCS insights (Graph API)
    try:
        r = ig_profiles.run()
        status["IG profiles"] = f"updated {r['ok']}/{r['total']}" if r["ok"] else "blocked this week (kept history)"
    except Exception as e:  # noqa: BLE001
        status["IG profiles"] = f"failed: {e.__class__.__name__}"
    status["LCS insights"] = ig_insights.run()

    LATEST.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    (HISTORY / f"{now.date().isoformat()}.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(status, indent=2))


if __name__ == "__main__":
    main()
