"""Copy Lab: free-text caption ideas, caption improvement and a viral-potential score.
Rule-based (no AI key needed). Scores are estimates built from social best-practice
signals (hook, format, shareability, emotion, CTA, hashtags, length), not predictions.
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


def hashtags(pillar: str, level: str, platform: str) -> list[str]:
    tags = TAGS[level][:3] + (TAGS["Faith"] if pillar in ("Faith & values", "Enrolment") else TAGS["Faith"][:1]) \
        + TAGS["Local"] + (TAGS["Parents"] if pillar in ("Enrolment", "Parents") else TAGS["Niche"][:1]) + TAGS["Niche"][:1]
    tags = list(dict.fromkeys(tags))
    return tags[:3] if platform == "Facebook" else tags[:11]


def viral_score(caption: str, fmt: str, platform: str) -> dict:
    t = caption or ""
    body = re.sub(r"#\w+", "", t).strip()
    first = body.split("\n")[0].strip()
    low = body.lower()
    tags = re.findall(r"#\w+", t)
    words = len(body.split())
    parts = {}
    hook = 0
    if first and len(first) <= 90:
        hook += 10
    if "?" in first:
        hook += 6
    if re.search(r"\b\d+\b", first):
        hook += 5
    if re.search(r"\b(you|your)\b", first.lower()):
        hook += 4
    parts["Hook"] = (min(hook, 25), 25)
    parts["Format"] = ({"Reel": 20, "Carousel": 15, "Story": 9, "Photo": 8, "Event": 8}.get(fmt, 8), 20)
    parts["Shareability"] = (min(sum(4 for w in SHARE if w in low), 15), 15)
    parts["Emotion & story"] = (min(sum(3 for w in EMO if w in low) + (3 if '"' in body else 0), 15), 15)
    parts["Call to action"] = (10 if any(w in low for w in CTA_WORDS) else 0, 10)
    lt = [x.lower() for x in tags]
    ok_n = (1 <= len(tags) <= 3) if platform == "Facebook" else (6 <= len(tags) <= 12)
    parts["Hashtags"] = ((5 if ok_n else 2 if tags else 0) + (3 if any(x in lt for x in TAGS["Local"]) else 0)
                         + (2 if any(x in lt for x in TAGS["Niche"] + TAGS["Faith"]) else 0), 10)
    good_len = (20 <= words <= 90) if platform == "Facebook" else (25 <= words <= 150)
    parts["Length"] = (5 if good_len else 2, 5)
    score = sum(v for v, _ in parts.values())
    label = ("High viral potential" if score >= 80 else "Good reach potential" if score >= 62
             else "Average" if score >= 45 else "Low reach potential")
    tips = []
    if parts["Hook"][0] < 15:
        tips.append("Open with a question or a number in the first line.")
    if parts["Format"][0] < 15:
        tips.append("Post it as a Reel or carousel: they reach far more people than single photos.")
    if parts["Shareability"][0] < 8:
        tips.append("Give people a reason to save or share (tips, a list, 'tag a family').")
    if parts["Emotion & story"][0] < 6:
        tips.append("Add a real moment or a parent/pupil quote.")
    if not parts["Call to action"][0]:
        tips.append("End with one clear action: book a visit, apply, comment.")
    if parts["Hashtags"][0] < 8:
        tips.append("Use " + ("1–3 hashtags on Facebook." if platform == "Facebook" else "8–12 hashtags, including #limerick and a niche tag."))
    return {"score": score, "label": label, "parts": parts, "tips": tips[:3], "words": words, "hashtags": len(tags)}


def ideas(prompt: str, level: str, platform: str, detail: str = "") -> list[dict]:
    _, topic = detect(prompt)
    lvl = level_of(prompt, level)
    pillar = TOPICS[topic]["pillar"]
    fmts = [TOPICS[topic]["fmt"], "Carousel" if TOPICS[topic]["fmt"] != "Carousel" else "Reel", "Photo" if platform == "Facebook" else "Story"]
    out = []
    lists = {"Enrolment": "✓ Learning at their own pace\n✓ Small classes and real attention\n✓ Christian values every day",
             "Student life": "✓ Daily goals they set themselves\n✓ Help the moment they need it\n✓ Progress they can see",
             "Faith & values": "✓ Chapel to start the week\n✓ Scripture in everyday learning\n✓ Serving others together",
             "Teachers": "✓ Knows every pupil by name\n✓ Checks progress every day\n✓ Celebrates every step",
             "Achievement": "✓ Every pace celebrated\n✓ Goals set and reached\n✓ Confidence that grows",
             "Events": "✓ Families together\n✓ Pupils leading the way\n✓ Memories for the whole year",
             "Parents": "✓ Small classes\n✓ Individual attention\n✓ A caring Christian community"}
    story = {"Enrolment": "\u201cThe supportive and caring environment has helped our son feel more confident.\u201d \u2013 an LCS parent",
             "Parents": "\u201cThe supportive and caring environment has helped our son feel more confident.\u201d \u2013 an LCS parent",
             "Student life": "One parent told us their son finally feels confident in himself. That's what learning at your own pace can do.",
             }
    share = {"Enrolment": "Know a family choosing a school? Tag them below 👇", "Parents": "Tag a family who's choosing a school 👇"}
    hk = HOOKS[topic]
    for i, h in enumerate([hk[0], hk[2], hk[1]]):  # question, list, story
        body = BODY[pillar]
        if lvl == "Primary":
            body = body.replace("primary and secondary", "primary")
        elif lvl == "Secondary":
            body = body.replace("primary and secondary", "secondary")
        cta = CTA[pillar] if platform == "Instagram" else CTA[pillar].replace("link in bio", "limerickchristianschool.com")
        if i == 0:      # question hook + share prompt
            sp = share.get(pillar, "Share this with a family who'd love it 💙")
            mid = [body] + ([] if "share" in cta.lower() or "tag" in cta.lower() else [sp])
        elif i == 1:    # list hook
            mid = [lists.get(pillar, lists["Enrolment"])] + ([] if "save" in cta.lower() else ["Save this post for later."])
        else:           # story hook
            mid = [story.get(pillar, "Real moments like this are why our families love being part of LCS."), body]
        tags = hashtags(pillar, lvl, platform)
        body_txt = "\n\n".join([h] + mid + ([detail.strip()] if detail and detail.strip() else []) + [cta])
        cap = body_txt + "\n\n" + " ".join(tags)
        sc = viral_score(cap, fmts[i], platform)
        out.append({"style": ["Question hook", "List hook", "Story hook"][i], "format": fmts[i], "caption": cap, "body": body_txt, "tags": tags, "score": sc,
                    "topic": topic, "level": lvl})
    return sorted(out, key=lambda x: -x["score"]["score"])


def improve(copy: str, level: str, platform: str, fmt: str = "Reel") -> dict:
    _, topic = detect(copy)
    lvl = level_of(copy, level)
    pillar = TOPICS[topic]["pillar"]
    before = viral_score(copy, fmt, platform)
    user_tags = re.findall(r"#\w+", copy)
    text = re.sub(r"#\w+", "", copy).strip()
    lines = [l.strip() for l in re.split(r"\n+|(?<=[.!?])\s+(?=[A-Z])", text) if l.strip()]
    changes = []
    first = lines[0] if lines else ""
    if not first or len(first) > 90 or ("?" not in first and not re.search(r"\d", first)):
        lines.insert(0, HOOKS[topic][0])
        changes.append("Added a scroll-stopping first line")
    if not any(k in text.lower() for k in ["lcs", "limerick christian", "own pace", "small class", "individual"]):
        lines.insert(2 if len(lines) > 1 else 1, BODY[pillar])
        changes.append("Added what makes LCS different")
    low = text.lower()
    if pillar in ("Enrolment", "Parents") and not any(w in low for w in SHARE):
        lines.append("Know a family choosing a school? Tag them below 👇")
        changes.append("Added a share prompt (tagging grows reach)")
    if not any(w in low for w in CTA_WORDS):
        cta = CTA[pillar] if platform == "Instagram" else CTA[pillar].replace("link in bio", "limerickchristianschool.com")
        lines.append(cta)
        changes.append("Added a clear call to action")
    if len(lines) > 1:
        changes.append("Split into short paragraphs for mobile reading")
    rec = hashtags(pillar, lvl, platform)
    tags = list(dict.fromkeys([t for t in user_tags if t.lower() not in [r.lower() for r in rec]][:2] + rec))
    tags = tags[:3] if platform == "Facebook" else tags[:11]
    if [t.lower() for t in tags] != [t.lower() for t in user_tags]:
        changes.append(f"Rebalanced hashtags ({len(tags)}: level, faith, local and niche)")
    new_body = "\n\n".join(lines)
    new = new_body + "\n\n" + " ".join(tags)
    after = viral_score(new, fmt, platform)
    alt = ideas(copy, level, platform)[:2]
    return {"before": before, "after": after, "caption": new, "body": new_body, "tags": tags, "original": copy,
            "changes": changes, "alternatives": alt, "topic": topic}
