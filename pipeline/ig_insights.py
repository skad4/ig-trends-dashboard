"""Optional: LCS's own Instagram insights via the official Instagram Graph API.

Needs two GitHub secrets (see README, "Connect LCS Instagram insights"):
  IG_ACCESS_TOKEN  long-lived token for the LCS Instagram professional account
  IG_USER_ID       the Instagram business account ID
Without them this step is skipped and the dashboard shows a "not connected" card.
Writes data/lcs_insights.json.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "lcs_insights.json"
API = "https://graph.facebook.com/v21.0"


def _get(path: str, token: str, **params) -> dict:
    r = requests.get(f"{API}/{path}", params={**params, "access_token": token}, timeout=30)
    r.raise_for_status()
    return r.json()


def run() -> str:
    token, uid = os.getenv("IG_ACCESS_TOKEN"), os.getenv("IG_USER_ID")
    if not token or not uid:
        return "not connected"
    out: dict = {"updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    try:
        out["profile"] = _get(uid, token, fields="username,followers_count,follows_count,media_count")
    except Exception as e:  # noqa: BLE001
        return f"failed: {e.__class__.__name__}"

    until = datetime.now(timezone.utc)
    since = until - timedelta(days=28)
    totals = {}
    for metric in ("reach", "profile_views", "website_clicks", "accounts_engaged", "total_interactions", "views"):
        try:
            j = _get(f"{uid}/insights", token, metric=metric, period="day", metric_type="total_value",
                     since=int(since.timestamp()), until=int(until.timestamp()))
            totals[metric] = j["data"][0]["total_value"]["value"]
        except Exception:  # noqa: BLE001  (metric not available for this account/version)
            pass
    out["last_28_days"] = totals

    demo = {}
    for bd in ("city", "age", "gender"):
        try:
            j = _get(f"{uid}/insights", token, metric="follower_demographics", period="lifetime",
                     metric_type="total_value", breakdown=bd)
            res = j["data"][0]["total_value"]["breakdowns"][0]["results"]
            demo[bd] = sorted(({"k": x["dimension_values"][0], "v": x["value"]} for x in res), key=lambda x: -x["v"])[:8]
        except Exception:  # noqa: BLE001
            pass
    out["followers_by"] = demo

    media = []
    try:
        j = _get(f"{uid}/media", token, fields="caption,media_type,media_product_type,timestamp,like_count,comments_count,permalink", limit=20)
        for m in j.get("data", []):
            row = {k: m.get(k) for k in ("media_type", "media_product_type", "timestamp", "like_count", "comments_count", "permalink")}
            row["caption"] = (m.get("caption") or "")[:80]
            try:
                ins = _get(f"{m['id']}/insights", token, metric="reach,saved,shares")
                for d in ins.get("data", []):
                    row[d["name"]] = d["values"][0]["value"]
            except Exception:  # noqa: BLE001
                pass
            media.append(row)
    except Exception:  # noqa: BLE001
        pass
    out["media"] = media

    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    return "updated"


if __name__ == "__main__":
    print(run())
