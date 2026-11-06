"""Weekly Instagram profile snapshot (public numbers only, no login).

For every school in data/benchmark.json, reads followers / following / total posts
from the public profile page and appends one row per school to data/ig_history.csv.
If Instagram blocks a request, that school is skipped this week (history is kept).
"""
from __future__ import annotations

import csv
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "data" / "benchmark.json"
HIST = ROOT / "data" / "ig_history.csv"
FIELDS = ["date", "handle", "followers", "following", "posts"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36",
    "Accept-Language": "en-IE,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml",
}
OG = re.compile(r'property="og:description"[^>]*content="([^"]+)"|content="([^"]+)"[^>]*property="og:description"')


def _num(s: str) -> int:
    s = s.replace(",", "").strip()
    mult = 1
    if s[-1:] in "KkMm":
        mult = 1_000 if s[-1] in "Kk" else 1_000_000
        s = s[:-1]
    return int(float(s) * mult)


def fetch_profile(handle: str) -> dict | None:
    try:
        r = requests.get(f"https://www.instagram.com/{handle}/", headers=HEADERS, timeout=30)
        m = OG.search(r.text)
        if not m:
            return None
        desc = m.group(1) or m.group(2)
        f = re.search(r"([\d.,KkMm]+)\s+Followers", desc)
        g = re.search(r"([\d.,KkMm]+)\s+Following", desc)
        p = re.search(r"([\d.,KkMm]+)\s+Posts", desc)
        if not f:
            return None
        return {"followers": _num(f.group(1)), "following": _num(g.group(1)) if g else None,
                "posts": _num(p.group(1)) if p else None}
    except Exception as e:  # noqa: BLE001
        print(f"[ig] {handle}: {e}")
        return None


def run() -> dict:
    schools = json.loads(BENCH.read_text())["schools"]
    today = datetime.now(timezone.utc).date().isoformat()
    rows, ok = [], 0
    for s in schools:
        d = fetch_profile(s["handle"])
        if d:
            ok += 1
            rows.append({"date": today, "handle": s["handle"], **d})
        time.sleep(2)
    if rows:
        existing = []
        if HIST.exists():
            with HIST.open() as fh:
                existing = [r for r in csv.DictReader(fh) if r["date"] != today]
        with HIST.open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=FIELDS)
            w.writeheader()
            for r in existing + rows:
                w.writerow({k: r.get(k) for k in FIELDS})
    print(f"[ig] profiles updated: {ok}/{len(schools)}")
    return {"ok": ok, "total": len(schools)}


if __name__ == "__main__":
    run()
