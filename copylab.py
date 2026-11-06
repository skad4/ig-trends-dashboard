"""Copy Lab: caption ideas, caption improvement and a reach score built on how
Instagram ranks content (2026).

Signals used (Adam Mosseri / Instagram, summarised by Buffer 2026):
- Watch time / attention: the first line or first 3 seconds decide everything.
- Sends per reach: shares by DM matter most for reaching NON-followers (Reels).
- Likes & comments per reach: matter most with existing followers (Feed posts).
- Saves: strong for carousels (unseen slides resurface later).
- Search: Instagram reads caption keywords, on-screen text and the profile.
- Hashtags: max 5 per post; they no longer drive reach, so keep them specific.
- Originality: original content is favoured over reposts.
Rule-based (no AI key). Scores are estimates, not predictions.
"""
from __future__ import annotations

import re

TOPICS = {
    "enrolment": {"kw": ["enrol", "enroll", "admission", "apply", "application", "places", "join", "offer", "fees", "new pupil", "new student"],
                  "pillar": "Enrolment", "fmt": "Reel"},
    "visit": {"kw": ["open day", "open morning", "visit", "tour", "come and see", "taster"], "pillar": "Enrolment", "fmt": "Reel"},
    "christmas": {"kw": ["christmas", "advent", "nativity", "carol", "festive"], "pillar": "Faith & values", "fmt": "Reel"},
    "easter": {"kw": ["easter", "good friday", "resurrection"], "pillar": "Faith & values", "fmt": "Carousel"},
    "faith": {"kw": ["faith", "chapel", "bible", "prayer", "jesus", "god", "verse", "christian"], "pillar": "Faith & values", "fmt": "Photo"},
    "teacher": {"kw": ["teacher", "staff", "principal", "meet"], "pillar": "Teachers", "fmt": "Reel"},
    "learning": {"kw": ["learn", "pace", "ace", "class", "curriculum", "study", "reading", "maths", "lesson"], "pillar": "Student life", "fmt": "Carousel"},
    "achievement": {"kw": ["award", "achiev", "well done", "congrat", "progress", "certificate", "result"], "pillar": "Achievement", "fmt": "Photo"},
    "event": {"kw": ["event", "trip", "sport", "concert", "show", "day out", "celebrat"], "pillar": "Events", "fmt": "Carousel"},
    "parents": {"kw": ["parent", "family", "families", "anxiety", "confidence", "testimonial"], "pillar": "Parents", "fmt": "Reel"},
}

HOOKS = {
    "enrolment": ["Looking for a school where your child is known by name?",
                  "Still deciding on a school for next year? Read this first.",
                  "3 reasons families are choosing Limerick Christian School 👇"],
    "visit": ["Come and see a normal school day. No sales pitch, just real classrooms.",
              "What does a morning at LCS actually look like?",
              "Visit us this week and meet the teachers 👋"],
    "christmas": ["The hope of Christmas, in our classrooms this week 🎄",
                  "Our pupils told the Christmas story their way.",
                  "5 moments from our Christmas week 👇"],
    "easter": ["Why Easter matters to us, in our pupils' words.",
               "He is risen: our Easter week in pictures.",
               "3 ways our pupils celebrated Easter this week"],
    "faith": ["How we start every school week.",
              "This week's verse, chosen by our pupils.",
              "Faith in action: what our pupils did for others this week"],
    "teacher": ["Meet the teacher who knows every pupil by name.",
                "3 quick questions with one of our teachers 👇",
                "7:45am, before anyone arrives…"],
    "learning": ["Every child moves forward at their own pace. Here's how.",
                 "What a small class really means for your child.",
                 "3 things parents notice in their child's first term with us 👇"],
    "achievement": ["Progress is celebrated here, at every pace 🌟",
                    "So proud of this week's milestones.",
                    "From September to now: look how far they've come"],
    "event": ["What a day! Here are our favourite moments 👇",
              "School is a community, and days like this show it.",
              "Swipe for the best photos from this week"],
    "parents": ["\"He feels confident again.\" A parent's story.",
                "Choosing a school? Ask these 5 questions.",
                "What parents tell us after the first month"],
}

BODY = {
    "Enrolment": "At LCS every pupil follows an individualised programme in small classes, with teachers who know them well. Applications are open for primary and secondary.",
    "Faith & values": "Christian values shape every school day, from chapel to the classroom.",
    "Teachers": "Our dedicated teachers give every pupil individual attention and support.",
    "Student life": "Pupils set their own goals each day and move on when they're ready, with support every step of the way.",
    "Achievement": "Every pupil progresses at their own pace, and every milestone is worth celebrating.",
    "Events": "Moments like these are what make our school a family.",
    "Parents": "We work alongside families so every child can grow in confidence and character.",
}

CTA = {
    "Enrolment": "Book a visit or apply today: link in bio.",
    "Faith & values": "Share this with someone who'd be encouraged by it 💙",
    "Teachers": "Follow along to meet the rest of our team.",
    "Student life": "Save this post and book a visit: link in bio.",
    "Achievement": "Join us in celebrating in the comments 👏",
    "Events": "Tag a family who'd love this!",
    "Parents": "Have a question? Send us a message, we're happy to help.",
}

TAGS = {
    "Primary": ["#primaryschool", "#irishprimaryschool", "#primaryeducation"],
    "Secondary": ["#secondaryschool", "#irishsecondaryschool", "#studentlife"],
    "Both": ["#irishschools", "#primaryschool", "#secondaryschool"],
    "Faith": ["#christianschool", "#christianeducation"],
    "Local": ["#limerick", "#lovelimerick", "#limerickschools"],
    "Parents": ["#irishparents", "#choosingaschool"],
    "Niche": ["#individuallearning", "#smallclasses"],
}

EMO = ["proud", "love", "hope", "confiden", "first", "journey", "family", "families", "joy", "grow", "flourish", "celebrat", "story", "heart", "real"]
SHARE = ["save", "share", "tag", "swipe", "👇", "tips", "reasons", "questions", "ways", "things"]
CTA_WORDS = ["link in bio", "book", "apply", "visit", "message", "dm", "comment", "tag", "share", "save", "follow", "register", "enrol", "join"]


def detect(text: str) -> tuple[str, str]:
    t = (text or "").lower()
    best, hits = "enrolment", 0
    for k, v in TOPICS.items():
        n = sum(1 for w in v["kw"] if w in t)
        if n > hits:
            best, hits = k, n
    intent = "improve" if (len(t) > 90 or "\n" in t or "#" in t) else "ideas"
    return intent, best


def level_of(text: str, default: str) -> str:
    t = (text or "").lower()
    if "primary" in t and "secondary" not in t:
        return "Primary"
    if "secondary" in t and "primary" not in t:
        return "Secondary"
    return default if default in ("Primary", "Secondary") else "Both"


FORMATS = ["Reel", "Carousel", "Post", "Story"]

# How Instagram ranks each format (shown in the app) and score weights per signal.
ALGO = {
    "Reel": {"reach": "Mostly non-followers", "signals": ["Watch time (hook in the first 3 seconds)", "Sends by DM", "Likes per reach"],
             "w": {"Attention hook": 25, "Sends (DM shares)": 20, "Likes & comments": 10, "Saves": 5, "Search keywords": 15,
                   "Original & local": 10, "Hashtags (max 5)": 5, "Caption length": 10},
             "tips": ["Put the hook on screen in the first 3 seconds; many people watch muted.",
                      "Keep it 15–60 seconds and use original audio or a voiceover.",
                      "End with a reason to send it: 'send this to a parent who…'."]},
    "Carousel": {"reach": "Followers + Explore", "signals": ["Saves", "Time spent swiping", "Likes & comments per reach"],
                 "w": {"Attention hook": 15, "Sends (DM shares)": 10, "Likes & comments": 15, "Saves": 20, "Search keywords": 15,
                       "Original & local": 10, "Hashtags (max 5)": 5, "Caption length": 10},
                 "tips": ["Make slide 1 a promise and slide 2 strong: Instagram re-shows unseen slides.",
                          "Use 5–10 slides with one idea each; add music to a photo carousel.",
                          "Close with 'save this for later' and one clear action."]},
    "Post": {"reach": "Mostly followers", "signals": ["Likes per reach", "Comments", "Profile visits"],
             "w": {"Attention hook": 15, "Sends (DM shares)": 10, "Likes & comments": 25, "Saves": 10, "Search keywords": 15,
                   "Original & local": 15, "Hashtags (max 5)": 5, "Caption length": 5},
             "tips": ["Use one strong, real photo (natural light, faces only with consent).",
                      "End with a simple question people can answer in the comments.",
                      "Reply to every comment in the first hour."]},
    "Story": {"reach": "Closest followers", "signals": ["Replies & sticker taps", "Viewing history", "DMs"],
              "w": {"Attention hook": 20, "Sticker / reply prompt": 30, "Sends (DM shares)": 15, "Original & local": 20, "Caption length": 15},
              "tips": ["Use a poll, question or link sticker: taps tell Instagram people care.",
                       "Keep text under 25 words per frame.",
                       "Post 1–3 frames during the school day; add a location sticker for Limerick."]},
}

KEYWORDS = ["school in limerick", "limerick school", "christian school", "primary school", "secondary school", "small class",
            "own pace", "individual", "enrol", "admission", "limerick", "lcs", "limerick christian school"]
SEND = ["send this", "send to", "share this", "share with", "tag a", "tag them", "tag someone", "know a family", "know a parent"]
SAVE = ["save this", "save for later", "save it", "swipe", "tips", "reasons", "questions", "steps", "ways", "things", "✓"]
TALK = ["comment", "tell us", "which", "what do you", "would you", "drop a", "reply", "?"]
STICKER = ["poll", "vote", "question sticker", "quiz", "slider", "link sticker", "reply", "tap"]
GENERIC_TAGS = {"#reels", "#explore", "#explorepage", "#viral", "#fyp", "#instagood", "#school", "#education", "#kids", "#fun"}


def hashtags(pillar: str, level: str, platform: str = "Instagram", fmt: str = "Reel") -> list[str]:
    """Max 5 on Instagram: 1 level · 1 faith · 1 local · 1 niche/parents · 1 level. Stories: 2."""
    niche = TAGS["Parents"][1] if pillar in ("Enrolment", "Parents") else TAGS["Niche"][0]
    tags = list(dict.fromkeys([TAGS[level][0], TAGS["Faith"][0], TAGS["Local"][0], niche, TAGS[level][1]]))
    return tags[:2] if fmt == "Story" else tags[:5]


def viral_score(caption: str, fmt: str = "Reel", platform: str = "Instagram") -> dict:
    fmt = fmt if fmt in ALGO else "Post"
    w = ALGO[fmt]["w"]
    t = caption or ""
    body = re.sub(r"#\w+", "", t).strip()
    first = body.split("\n")[0].strip()
    low = body.lower()
    last = [l for l in body.split("\n") if l.strip()][-1].lower() if body else ""
    tags = re.findall(r"#\w+", t)
    words = len(body.split())
    raw = {}
    h = (0.4 if first and len(first) <= 90 else 0) + (0.25 if "?" in first else 0) + (0.2 if re.search(r"\b\d+\b", first) else 0) \
        + (0.15 if re.search(r"\b(you|your)\b", first.lower()) else 0) + (0.1 if re.search(r"[\U0001F300-\U0001FAFF👇]", first) else 0)
    raw["Attention hook"] = min(h, 1)
    raw["Sends (DM shares)"] = 1 if any(x in low for x in SEND) else 0
    raw["Likes & comments"] = min((0.6 if any(x in last for x in TALK) else 0) + (0.4 if any(e in low for e in ["proud", "celebrat", "love", "hope", "confiden", "\u201c", '"']) else 0), 1)
    raw["Saves"] = min(sum(0.35 for x in SAVE if x in low), 1)
    raw["Search keywords"] = min(sum(1 for k in KEYWORDS if k in low) / 3, 1)
    raw["Original & local"] = min((0.5 if any(x in low for x in ["our ", "we ", "lcs", "limerick christian"]) else 0)
                                  + (0.5 if any(x in low for x in ["limerick", "pupils", "teachers", "classroom", "chapel"]) else 0), 1)
    lt = {x.lower() for x in tags}
    raw["Hashtags (max 5)"] = 0 if len(tags) > 5 else (1 if 3 <= len(tags) <= 5 and not (lt & GENERIC_TAGS) else 0.5 if tags else 0)
    raw["Sticker / reply prompt"] = 1 if any(x in low for x in STICKER) else 0
    rng = {"Reel": (8, 80), "Carousel": (30, 150), "Post": (20, 125), "Story": (1, 25)}[fmt]
    raw["Caption length"] = 1 if rng[0] <= words <= rng[1] else 0.4
    parts = {k: (round(raw[k] * m), m) for k, m in w.items()}
    score = sum(v for v, _ in parts.values())
    label = ("High viral potential" if score >= 80 else "Good reach potential" if score >= 62
             else "Average" if score >= 45 else "Low reach potential")
    tip_map = {
        "Attention hook": "Start with a short question or number: the first line (or first 3 seconds) decides if people stop.",
        "Sends (DM shares)": "Add a reason to send it by DM ('Send this to a parent choosing a school'). Sends are the top signal for new reach.",
        "Likes & comments": "End with a question parents can answer in the comments.",
        "Saves": "Make it worth saving: a list, tips or '5 questions to ask', plus 'save this for later'.",
        "Search keywords": "Write the words parents search for: 'Christian school in Limerick', 'primary school', 'secondary school'.",
        "Original & local": "Show something only LCS has: our pupils, teachers, classrooms in Limerick.",
        "Hashtags (max 5)": "Use 3–5 specific hashtags (Instagram allows 5); avoid #reels, #explore, #viral.",
        "Sticker / reply prompt": "Add a poll or question sticker so followers tap and reply.",
        "Caption length": f"Aim for {rng[0]}–{rng[1]} words for a {fmt.lower()}.",
    }
    gaps = sorted(parts.items(), key=lambda kv: kv[1][0] / kv[1][1])
    tips = [tip_map[k] for k, (v, m) in gaps if v < m * 0.6][:3]
    return {"score": score, "label": label, "parts": parts, "tips": tips, "words": words, "hashtags": len(tags), "format": fmt}


KW_LINE = {"Primary": "A Christian primary school in Limerick where every child learns at their own pace.",
           "Secondary": "A Christian secondary school in Limerick with small classes and individual support.",
           "Both": "A Christian school in Limerick for primary and secondary pupils, with small classes and learning at their own pace."}
SEND_LINE = {"Enrolment": "Send this to a parent who's choosing a school 💙", "Parents": "Send this to a parent who's choosing a school 💙",
             "Faith & values": "Send this to someone who'd be encouraged by it 💙", "Teachers": "Send this to someone who'd love to meet our team.",
             "Student life": "Send this to a parent who'd love this for their child.", "Achievement": "Send this to someone who'd be proud too 👏",
             "Events": "Send this to a family who was there!"}
QUESTION = {"Enrolment": "What matters most to you when choosing a school?", "Parents": "What would you ask on a school visit?",
            "Faith & values": "What's a verse that encourages you this week?", "Teachers": "What question should we ask our teachers next?",
            "Student life": "What did your child love learning this week?", "Achievement": "Join us in celebrating: drop a 👏 below!",
            "Events": "Which moment was your favourite?"}
STICKER_LINE = {"Enrolment": "Poll: Have you visited a school yet? Yes / Not yet", "Parents": "Question sticker: Ask us anything about LCS",
                "Faith & values": "Slider: How encouraged do you feel today?", "Teachers": "Question sticker: Ask our teacher a question",
                "Student life": "Poll: Reading corner or maths corner?", "Achievement": "Slider: How proud are you? 💙",
                "Events": "Quiz: Guess how many pupils took part!"}


def _caption(fmt: str, style: int, topic: str, pillar: str, lvl: str, detail: str) -> str:
    hk = HOOKS[topic]
    hook = [hk[0], hk[2], hk[1]][style]
    body = BODY[pillar].replace("primary and secondary", {"Primary": "primary", "Secondary": "secondary"}.get(lvl, "primary and secondary"))
    lists = {"Enrolment": "✓ Learning at their own pace\n✓ Small classes and real attention\n✓ Christian values every day",
             "Student life": "✓ Daily goals they set themselves\n✓ Help the moment they need it\n✓ Progress they can see",
             "Faith & values": "✓ Chapel to start the week\n✓ Scripture in everyday learning\n✓ Serving others together",
             "Teachers": "✓ Knows every pupil by name\n✓ Checks progress every day\n✓ Celebrates every step",
             "Achievement": "✓ Every pace celebrated\n✓ Goals set and reached\n✓ Confidence that grows",
             "Events": "✓ Families together\n✓ Pupils leading the way\n✓ Memories for the whole year",
             "Parents": "✓ Small classes\n✓ Individual attention\n✓ A caring Christian community"}
    quote = "\u201cThe supportive and caring environment has helped our son feel more confident.\u201d \u2013 an LCS parent"
    cta = CTA[pillar]
    if fmt == "Reel" and any(x in cta.lower() for x in ("share", "tag")):
        cta = "Follow us for more from our school week."  # the send prompt already asks for shares
    det = [detail.strip()] if detail and detail.strip() else []
    if fmt == "Story":
        return "\n\n".join([hook[:90]] + det + [f"[{STICKER_LINE[pillar]}]", "Link sticker: limerickchristianschool.com"])
    mid = [body] if style == 0 else [lists[pillar]] if style == 1 else [quote if pillar in ("Enrolment", "Parents", "Student life") else
                                                                       "Real moments like this are why our families love being part of LCS.", body]
    kw = KW_LINE[lvl]
    if fmt == "Reel":      # short caption, keywords for search, ends on a send prompt
        parts = [hook, kw] + det + [SEND_LINE[pillar], cta]
    elif fmt == "Carousel":  # swipe + save
        parts = [hook + " Swipe →"] + mid + [kw] + det + ["Save this post for later.", cta]
    else:                  # Post: conversation
        parts = [hook] + mid + [kw] + det + [cta, QUESTION[pillar]]
    return "\n\n".join(dict.fromkeys(parts))


def ideas(prompt: str, level: str, platform: str = "Instagram", detail: str = "", fmt: str = "Reel") -> list[dict]:
    _, topic = detect(prompt)
    lvl = level_of(prompt, level)
    pillar = TOPICS[topic]["pillar"]
    out = []
    for i, style in enumerate(["Question hook", "List hook", "Story hook"]):
        body_txt = _caption(fmt, i, topic, pillar, lvl, detail)
        tags = hashtags(pillar, lvl, platform, fmt)
        cap = body_txt + "\n\n" + " ".join(tags)
        out.append({"style": style, "format": fmt, "caption": cap, "body": body_txt, "tags": tags,
                    "score": viral_score(cap, fmt, platform), "topic": topic, "level": lvl})
    return sorted(out, key=lambda x: -x["score"]["score"])


def improve(copy: str, level: str, platform: str = "Instagram", fmt: str = "Reel") -> dict:
    _, topic = detect(copy)
    lvl = level_of(copy, level)
    pillar = TOPICS[topic]["pillar"]
    before = viral_score(copy, fmt, platform)
    user_tags = re.findall(r"#\w+", copy)
    text = re.sub(r"#\w+", "", copy).strip()
    lines = [l.strip() for l in re.split(r"\n+|(?<=[.!?])\s+(?=[A-Z])", text) if l.strip()]
    low = text.lower()
    changes = []
    first = lines[0] if lines else ""
    if not first or len(first) > 90 or ("?" not in first and not re.search(r"\d", first)):
        lines.insert(0, HOOKS[topic][0])
        changes.append("New first line: a short question that stops the scroll (attention)")
    if fmt == "Story":
        lines = [l[:90] for l in lines[:2]]
        if not any(x in low for x in STICKER):
            lines.append(f"[{STICKER_LINE[pillar]}]")
            changes.append("Added a sticker idea (replies and taps rank Stories)")
    else:
        if sum(1 for k in KEYWORDS if k in low) < 2:
            lines.insert(2 if len(lines) > 1 else 1, KW_LINE[lvl])
            changes.append("Added search keywords ('Christian school in Limerick'): Instagram reads captions for search")
        if fmt == "Reel" and not any(x in low for x in SEND):
            lines.append(SEND_LINE[pillar])
            changes.append("Added a send prompt: DM shares are the top signal for reaching new people")
        if fmt == "Carousel" and not any(x in low for x in SAVE):
            lines.append("Save this post for later.")
            changes.append("Added a save prompt: saves push carousels")
        if not any(w in low for w in CTA_WORDS):
            lines.append(CTA[pillar])
            changes.append("Added one clear call to action")
        if fmt == "Post" and not any(x in (lines[-1].lower() if lines else "") for x in TALK):
            lines.append(QUESTION[pillar])
            changes.append("Ends with a question: comments and likes rank feed posts")
    rec = hashtags(pillar, lvl, platform, fmt)
    keep = [t for t in user_tags if t.lower() not in {r.lower() for r in rec} and t.lower() not in GENERIC_TAGS][:1]
    limit = 2 if fmt == "Story" else 5
    tags = list(dict.fromkeys(rec[:limit - len(keep)] + keep))[:limit]
    if [t.lower() for t in tags] != [t.lower() for t in user_tags]:
        dropped = [t for t in user_tags if t.lower() in GENERIC_TAGS]
        changes.append(f"Hashtags: {len(tags)} specific tags (max 5)" + (f"; removed generic {' '.join(dropped)}" if dropped else ""))
    new_body = "\n\n".join(dict.fromkeys(lines))
    new = new_body + "\n\n" + " ".join(tags)
    return {"before": before, "after": viral_score(new, fmt, platform), "caption": new, "body": new_body, "tags": tags,
            "original": copy, "changes": changes, "topic": topic, "format": fmt}
