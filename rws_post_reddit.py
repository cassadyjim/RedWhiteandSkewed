#!/usr/bin/env python3
"""
Post a published Red White & Skewed story to Reddit.

Usage:
    python3 rws_post_reddit.py 2026-11-24-jobs-report-inflation-paychecks-divide.json
    python3 rws_post_reddit.py            # newest 2026-*.json in this folder

SAFETY: DRY RUN by default. Nothing is posted unless REDDIT_POST_LIVE=1.
Posts are text (self) posts: both opposing headlines as the hook, the story
body, sources, and a link back to the full story. One post per subreddit per
story; already-posted pairs are recorded in state/reddit_posted.json.

Env vars (Reddit "script" app, https://www.reddit.com/prefs/apps):
    REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME, REDDIT_PASSWORD
    REDDIT_SUBREDDITS   comma list (default: PoliticalHumor,neutral_politics,MediaBias)
    REDDIT_POST_LIVE    "1" to really post
    REDDIT_POST_DELAY   seconds between subreddit posts (default 600)
    REDDIT_FLAIRS       optional JSON, e.g. {"PoliticalHumor": "<flair_template_id>"}

Failures never raise out of main(): this must not break story publishing.
"""
import html
import json
import os
import re
import sys
import time
from pathlib import Path

import requests

SCRIPT_DIR = Path(__file__).parent
STATE_FILE = SCRIPT_DIR / "state" / "reddit_posted.json"
SITE = "https://www.redwhiteandskewed.com"
UA = "script:rws-story-poster:v1.0 (by /u/{user})"
DEFAULT_SUBS = "PoliticalHumor,neutral_politics,MediaBias"
MAX_BODY = 38000  # Reddit self-post limit is 40,000 chars


def log(msg):
    print(f"[reddit] {msg}", flush=True)


def html_to_md(s):
    """Convert the story HTML snippets to Reddit markdown."""
    s = re.sub(r'<a [^>]*href="([^"]+)"[^>]*>(.*?)</a>', r"[\2](\1)", s, flags=re.S)
    s = re.sub(r"<(strong|b)>(.*?)</\1>", r"**\2**", s, flags=re.S)
    s = re.sub(r"<(em|i)>(.*?)</\1>", r"*\2*", s, flags=re.S)
    s = re.sub(r"<br\s*/?>", "\n", s)
    s = re.sub(r"</p>", "\n\n", s)
    s = re.sub(r"<[^>]+>", "", s)
    return html.unescape(s).strip()


def story_url(path):
    return f"{SITE}/stories/{path.stem}.html"


def build_post(story, path):
    cons, lib = story["conservative"], story["liberal"]
    title = f'"{cons["headline"]}" vs. "{lib["headline"]}"'
    if len(title) > 300:  # Reddit title limit
        title = f'{cons["headline"]} / {lib["headline"]}'[:297] + "..."
    url = story_url(path)

    def side(label, d):
        paras = "\n\n".join(html_to_md(p) for p in d["paragraphs"])
        return f'## {label}: {d["headline"]}\n\n*{d.get("byline", "")}*\n\n{paras}'

    fc = story.get("factcheck", {})
    fc_md = "\n\n".join(html_to_md(p) for p in fc.get("paragraphs", []))
    parts = [
        f'**{story["title"]}**',
        f'*{story.get("subtitle", "")}*',
        "Same news, two headlines. Here is how each side is spinning it, then the fact-check.",
        side("The Right", cons),
        side("The Left", lib),
    ]
    if fc_md:
        parts.append(f'## Fact check: {fc.get("headline", "")}\n\n{fc_md}')
    parts.append(
        f"---\n\nFull story with sources and reader poll: {url}\n\n"
        "*I write Red White & Skewed. Happy to discuss sourcing in the comments.*"
    )
    body = "\n\n".join(p for p in parts if p)
    if len(body) > MAX_BODY:
        body = body[:MAX_BODY].rsplit("\n\n", 1)[0] + f"\n\n*(trimmed, full story: {url})*"
    return title, body


def load_posted():
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {}


def save_posted(d):
    STATE_FILE.parent.mkdir(exist_ok=True)
    STATE_FILE.write_text(json.dumps(d, indent=2))


def get_token(user):
    r = requests.post(
        "https://www.reddit.com/api/v1/access_token",
        auth=(os.environ["REDDIT_CLIENT_ID"], os.environ["REDDIT_CLIENT_SECRET"]),
        data={"grant_type": "password", "username": user,
              "password": os.environ["REDDIT_PASSWORD"]},
        headers={"User-Agent": UA.format(user=user)},
        timeout=30,
    )
    r.raise_for_status()
    tok = r.json().get("access_token")
    if not tok:
        raise RuntimeError(f"No token: {r.text[:200]}")
    return tok


def submit(token, user, sub, title, body, flair_id=None):
    data = {"sr": sub, "kind": "self", "title": title, "text": body,
            "api_type": "json", "resubmit": "true"}
    if flair_id:
        data["flair_id"] = flair_id
    r = requests.post(
        "https://oauth.reddit.com/api/submit", data=data,
        headers={"Authorization": f"bearer {token}",
                 "User-Agent": UA.format(user=user)},
        timeout=30,
    )
    r.raise_for_status()
    j = r.json().get("json", {})
    if j.get("errors"):
        raise RuntimeError(str(j["errors"]))
    return j["data"]["url"]


def main():
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
        if not path.is_absolute():
            path = SCRIPT_DIR / path
    else:
        files = sorted(SCRIPT_DIR.glob("2026-*.json"))
        if not files:
            log("No story files found")
            return 0
        path = files[-1]
    story = json.loads(path.read_text())
    title, body = build_post(story, path)
    subs = [s.strip() for s in (os.environ.get("REDDIT_SUBREDDITS") or DEFAULT_SUBS).split(",") if s.strip()]
    live = os.environ.get("REDDIT_POST_LIVE") == "1"
    flairs = json.loads(os.environ.get("REDDIT_FLAIRS", "{}") or "{}")
    delay = int(os.environ.get("REDDIT_POST_DELAY", "600"))

    if not live:
        log(f"DRY RUN (set REDDIT_POST_LIVE=1 to post). Story: {path.name}")
        log(f"Subreddits: {', '.join(subs)}")
        log(f"Title ({len(title)} chars): {title}")
        log(f"Body: {len(body)} chars\n{'-' * 60}\n{body[:1500]}\n{'-' * 60}")
        return 0

    missing = [k for k in ("REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET",
                           "REDDIT_USERNAME", "REDDIT_PASSWORD") if not os.environ.get(k)]
    if missing:
        log(f"Missing env vars: {', '.join(missing)} — skipping")
        return 0

    user = os.environ["REDDIT_USERNAME"]
    posted = load_posted()
    done = posted.setdefault(path.stem, {})
    try:
        token = get_token(user)
    except Exception as e:
        log(f"Auth failed: {e}")
        return 0

    first = True
    for sub in subs:
        if sub in done:
            log(f"r/{sub}: already posted, skipping")
            continue
        if not first:
            time.sleep(delay)  # avoid Reddit rate limits / spam filters
        first = False
        try:
            done[sub] = submit(token, user, sub, title, body, flairs.get(sub))
            log(f"r/{sub}: posted {done[sub]}")
        except Exception as e:
            log(f"r/{sub}: FAILED {e}")
        save_posted(posted)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        log(f"Unexpected error (non-fatal): {e}")
        sys.exit(0)
