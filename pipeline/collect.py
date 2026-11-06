"""Collectors for public, free trend sources.

Each collector returns a dict (or None if it failed). A failure never breaks the
pipeline: run_weekly.py keeps the previous week's data for that source.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ig-trends-dashboard/1.0; weekly personal research)",
    "Accept-Language": "en-IE,en;q=0.9",
}
TIMEOUT = 30

CREATORDB_URL = "https://creatordb.app/free-tools/trending-instagram-audio/"
SOCIALPILOT_URL = "https://www.socialpilot.co/blog/instagram-reels-trends"
KWORB_IE_URL = "https://kworb.net/spotify/country/ie_weekly.html"


def _get(url: str) -> str:
    r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    if "charset" not in r.headers.get("Content-Type", "").lower():
        r.encoding = "utf-8"  # requests defaults to latin-1 otherwise (breaks É, Í…)
    return r.text


def _cell_lines(cell) -> list[str]:
    return [t.strip() for t in cell.get_text("\n").split("\n") if t.strip()]


def _to_int(text: str | None) -> int | None:
    if not text:
        return None
    m = re.search(r"([\d.,]+)\s*([KkMm]?)", text)
    if not m:
        return None
    num = float(m.group(1).replace(",", ""))
    mult = {"k": 1_000, "m": 1_000_000}.get(m.group(2).lower(), 1)
    return int(num * mult)


def norm_title(s: str) -> str:
    s = s.lower()
    s = re.sub(r"\(.*?\)|\[.*?\]", "", s)
    s = re.sub(r"[^a-z0-9 ]", "", s)
    return re.sub(r"\s+", " ", s).strip()


# --------------------------------------------------------------------------- #
# 1) CreatorDB weekly trending Instagram audio
# --------------------------------------------------------------------------- #
def collect_creatordb() -> dict | None:
    try:
        soup = BeautifulSoup(_get(CREATORDB_URL), "lxml")
    except Exception as e:  # noqa: BLE001
        print(f"[creatordb] fetch failed: {e}")
        return None

    best = None
    for table in soup.find_all("table"):
        headers = [h.get_text(" ", strip=True).lower() for h in table.find_all("th")]
        if any("audio" in h or "sound" in h for h in headers):
            best = (table, headers)
            break
    if not best:
        print("[creatordb] no audio table found")
        return None

    table, headers = best

    def idx(*names):
        for i, h in enumerate(headers):
            if any(n in h for n in names):
                return i
        return None

    i_rank, i_audio, i_artist = idx("#", "rank"), idx("audio", "sound"), idx("artist")
    i_trend, i_heat, i_mom = idx("trend"), idx("heat"), idx("momentum")
    i_also, i_reels = idx("also", "chart"), idx("reels")

    items = []
    for row in table.find_all("tr"):
        cells = row.find_all(["td"])
        if len(cells) < 3:
            continue
        get = lambda i: cells[i] if i is not None and i < len(cells) else None  # noqa: E731
        audio_lines = _cell_lines(get(i_audio)) if get(i_audio) else []
        title = audio_lines[0] if audio_lines else ""
        artist = (
            " ".join(_cell_lines(get(i_artist))) if get(i_artist)
            else (audio_lines[1] if len(audio_lines) > 1 else "")
        )
        if not title:
            continue
        heat_txt = get(i_heat).get_text(" ", strip=True) if get(i_heat) else ""
        items.append({
            "rank": _to_int(get(i_rank).get_text(strip=True)) if get(i_rank) else len(items) + 1,
            "title": title,
            "artist": artist,
            "trend": " ".join(_cell_lines(get(i_trend))) if get(i_trend) else "",
            "heat": _to_int(heat_txt),
            "momentum": get(i_mom).get_text(" ", strip=True) if get(i_mom) else "",
            "also_charting": "; ".join(_cell_lines(get(i_also))) if get(i_also) else "",
            "reels": _to_int(get(i_reels).get_text(" ", strip=True)) if get(i_reels) else None,
        })

    if len(items) < 3:
        print(f"[creatordb] parsed only {len(items)} rows, ignoring")
        return None

    # Example reels ("Reels Using These Sounds": numbers match the chart)
    by_rank: dict[int, list[str]] = {}
    for node in soup.find_all("a", href=True):
        if "instagram.com/reel/" not in node["href"]:
            continue
        code = re.search(r"/reel/([A-Za-z0-9_-]+)", node["href"])
        num = re.match(r"\s*0?(\d{1,2})\b", node.get_text("\n", strip=True))
        if code and num:
            lst = by_rank.setdefault(int(num.group(1)), [])
            if code.group(1) not in lst:
                lst.append(code.group(1))
    for it in items:
        it["example_reels"] = by_rank.get(it["rank"], [])[:3]

    m = re.search(r"week of ([A-Z][a-z]+ \d{1,2},? \d{4})", soup.get_text(" "), re.I)
    return {
        "source": "CreatorDB",
        "url": CREATORDB_URL,
        "week_label": m.group(1) if m else None,
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "items": items,
    }


# --------------------------------------------------------------------------- #
# 2) SocialPilot weekly Reels trends (business use + content ideas)
# --------------------------------------------------------------------------- #
HEADING_RE = re.compile(r"^\s*(\d{1,2})[.)]\s*[\"“]?(.+?)[\"”]?\s+(?:by|[-–—:])\s+(.+?)\s*$", re.I)


def collect_socialpilot() -> dict | None:
    try:
        soup = BeautifulSoup(_get(SOCIALPILOT_URL), "lxml")
    except Exception as e:  # noqa: BLE001
        print(f"[socialpilot] fetch failed: {e}")
        return None

    items = []
    for h in soup.find_all(["h2", "h3", "h4"]):
        m = HEADING_RE.match(h.get_text(" ", strip=True))
        if not m:
            continue
        fields, desc, ideas = {}, [], []
        for sib in h.find_next_siblings():
            if sib.name in ("h2", "h3", "h4"):
                break
            if sib.name in ("ul", "ol"):
                ideas += [li.get_text(" ", strip=True) for li in sib.find_all("li")]
                continue
            t = sib.get_text(" ", strip=True)
            lm = re.match(r"^([A-Za-z][A-Za-z ]{1,25}):\s*(.*)$", t)
            if lm:
                fields[lm.group(1).strip().lower()] = lm.group(2).strip()
            elif t:
                desc.append(t)

        def f(*keys):
            for k in keys:
                for fk, v in fields.items():
                    if fk.startswith(k):
                        return v
            return ""

        items.append({
            "rank": int(m.group(1)),
            "title": m.group(2).strip(),
            "artist": m.group(3).strip(),
            "stage": f("stage", "trend stage"),
            "mood": f("mood", "vibe"),
            "best_for": f("best for", "ideal for"),
            "idea": ideas[0] if ideas else (desc[0][:220] if desc else ""),
            "ideas": ideas[:5],
            "about": desc[0][:400] if desc else "",
            "reels": _to_int(f("post count", "reels", "uses")),
        })

    # de-duplicate by rank, keep first
    seen, dedup = set(), []
    for it in items:
        if it["rank"] not in seen:
            seen.add(it["rank"])
            dedup.append(it)

    if len(dedup) < 3:
        print(f"[socialpilot] parsed only {len(dedup)} sounds, ignoring")
        return None
    return {
        "source": "SocialPilot",
        "url": SOCIALPILOT_URL,
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "items": sorted(dedup, key=lambda x: x["rank"])[:20],
    }


# --------------------------------------------------------------------------- #
# 3) Kworb — Spotify weekly chart, Ireland (regional proxy for audio)
# --------------------------------------------------------------------------- #
def collect_kworb_ie(limit: int = 50) -> dict | None:
    try:
        soup = BeautifulSoup(_get(KWORB_IE_URL), "lxml")
    except Exception as e:  # noqa: BLE001
        print(f"[kworb] fetch failed: {e}")
        return None

    table = soup.find("table")
    if table is None:
        print("[kworb] no table")
        return None

    heads = [th.get_text(strip=True).lower() for th in table.find_all("th")]

    def col(name, default):
        return heads.index(name) if name in heads else default

    i_wks, i_pk, i_str = col("wks", 3), col("pk", 4), col("streams", 6)
    items = []
    for row in table.find_all("tr"):
        tds = row.find_all("td")
        if len(tds) <= max(i_str, 5):
            continue
        pos = _to_int(tds[0].get_text(strip=True))
        change = tds[1].get_text(strip=True)
        artist_title = tds[2].get_text(" ", strip=True)
        if " - " in artist_title:
            artist, title = artist_title.split(" - ", 1)
        else:
            artist, title = "", artist_title
        items.append({
            "pos": pos,
            "change": change or "=",
            "artist": artist.strip(),
            "title": title.strip(),
            "weeks": _to_int(tds[i_wks].get_text(strip=True)),
            "peak": tds[i_pk].get_text(" ", strip=True),
            "streams": int(re.sub(r"[^\d]", "", tds[i_str].get_text(strip=True)) or 0),
        })
        if len(items) >= limit:
            break

    if len(items) < 10:
        print(f"[kworb] parsed only {len(items)} rows, ignoring")
        return None

    m = re.search(r"(\d{4}/\d{2}/\d{2})", soup.get_text(" "))
    return {
        "source": "Kworb (Spotify Weekly Chart — Ireland)",
        "url": KWORB_IE_URL,
        "chart_date": m.group(1) if m else None,
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "items": items,
    }


def cross_reference(creatordb: dict | None, kworb: dict | None) -> None:
    """Annotate each Reels audio with its position in the Irish Spotify chart."""
    if not creatordb or not kworb:
        return
    ie = {norm_title(i["title"]): i for i in kworb["items"]}
    for a in creatordb["items"]:
        hit = ie.get(norm_title(a["title"]))
        a["ireland_pos"] = hit["pos"] if hit else None
        a["ireland_change"] = hit["change"] if hit else None
