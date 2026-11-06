"""Apply a Chrome Instagram scan to the dashboard data.

Usage: python tools/apply_scan.py scan.json
scan.json = {"<handle>": <JSON object returned by tools/ig_scan.js>, ...}
Updates data/benchmark.json (stats per school) and appends to data/ig_history.csv.
Schools missing from the scan keep their previous values.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BENCH, HIST = ROOT / "data" / "benchmark.json", ROOT / "data" / "ig_history.csv"
FIELDS = ["date", "handle", "followers", "following", "posts", "avg_eng", "reels_share", "source"]


def n(s: str) -> int:
    s = s.replace(",", "")
    m = 1000 if s.endswith("K") else 1_000_000 if s.endswith("M") else 1
    return int(float(s.rstrip("KM")) * m)


def main(path: str) -> None:
    scan = json.loads(Path(path).read_text())
    bm = json.loads(BENCH.read_text())
    today = date.today().isoformat()
    rows, updated = [], 0
    for s in bm["schools"]:
        r = scan.get(s["handle"])
        if not r or not r.get("og"):
            continue
        f = re.search(r"([\d.,KM]+) Followers", r["og"]); g = re.search(r"([\d.,KM]+) Following", r["og"]); p = re.search(r"([\d.,KM]+) Posts", r["og"])
        if not f:
            continue
        s["followers"] = n(f.group(1))
        if p:
            s["posts_total"] = n(p.group(1))
        if r.get("n"):
            s.update({"sample": r["n"], "reels": r["reels"], "avg_eng": r["avgEng"], "avg_reel": r["avgReel"], "avg_post": r["avgPost"],
                      "per_week": min(r["perWeek"] or 0, 7.0), "last_post": r["last"] or s.get("last_post"),
                      "pillars": r["pil"], "pillar_eng": r["pilEng"], "top": r["top"] or s.get("top", [])})
        rows.append({"date": today, "handle": s["handle"], "followers": s["followers"], "following": n(g.group(1)) if g else "",
                     "posts": s.get("posts_total", ""), "avg_eng": s.get("avg_eng", ""),
                     "reels_share": round(r["reels"] / r["n"], 2) if r.get("n") else "", "source": "chrome"})
        updated += 1
    bm["captured"] = today
    BENCH.write_text(json.dumps(bm, indent=2, ensure_ascii=False))
    old = []
    if HIST.exists():
        with HIST.open() as fh:
            done = {r["handle"] for r in rows}
            old = [x for x in csv.DictReader(fh) if not (x["date"] == today and x["handle"] in done)]
    with HIST.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        for x in old + rows:
            w.writerow({k: x.get(k, "") for k in FIELDS})
    print(f"updated {updated}/{len(bm['schools'])} schools")


if __name__ == "__main__":
    main(sys.argv[1])
