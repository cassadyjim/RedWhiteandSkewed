#!/usr/bin/env python3
"""
Red White & Skewed — Daily Story Automation
Runs at 10 PM nightly via Mac cron job.

Usage:
    python3 rws_daily_auto.py              # Normal daily run
    python3 rws_daily_auto.py --test-email # Send test email only
    python3 rws_daily_auto.py --force      # Run even if already ran today
"""

import os
import json
import smtplib
import ssl
import datetime
import pathlib
import re
import subprocess
import sys
import argparse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib.request import urlopen, Request
from urllib.error import URLError
import time

SCRIPT_DIR = pathlib.Path(__file__).parent
HISTORY_FILE = SCRIPT_DIR / "story_history.json"
LOG_FILE = pathlib.Path("/tmp/rws_daily_auto.log")
LOCK_FILE = pathlib.Path("/tmp/rws_daily.lock")
STATE_FILE = SCRIPT_DIR / "state" / "pending_story.json"

# In GitHub Actions, lock file is always fresh (ephemeral /tmp), so no issue
GITHUB_ACTIONS = os.environ.get("GITHUB_ACTIONS") == "true"

ENV = {}


def log_message(message):
    """Write message to log file with timestamp."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}\n"
    print(log_entry.rstrip())
    try:
        with open(LOG_FILE, "a") as f:
            f.write(log_entry)
    except Exception as e:
        print(f"Failed to write to log: {e}")


def load_env():
    """Load credentials from os.environ (GitHub Actions) and/or .env file."""
    global ENV

    # Load from os.environ first — used when running in GitHub Actions
    env_keys = [
        "ANTHROPIC_API_KEY", "PEXELS_API_KEY",
        "SMTP_HOST", "SMTP_PORT", "SMTP_FROM", "SMTP_PASSWORD",
        "IMAP_HOST", "IMAP_PORT", "IMAP_USER", "IMAP_PASSWORD",
        "RWS_SFTP_HOST", "RWS_SFTP_USERNAME", "RWS_SFTP_PASSWORD",
        "WIX_API_KEY", "WIX_SITE_ID", "WIX_COLLECTION_ID",
        "GITHUB_TOKEN", "GITHUB_REPO",
    ]
    for key in env_keys:
        val = os.environ.get(key)
        if val:
            ENV[key] = val.strip()  # strip newlines/spaces (GitHub Secrets can have trailing newlines)

    # Then load from .env file — overrides os.environ if both present (local dev)
    env_path = SCRIPT_DIR / ".env"
    if not env_path.exists():
        if ENV:
            log_message(f"No .env file found; using {len(ENV)} env vars from environment")
        else:
            log_message("Warning: .env file not found and no env vars set")
        return

    try:
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    ENV[key] = value
        log_message(f"Loaded {len(ENV)} env variables")
    except Exception as e:
        log_message(f"Error loading .env file: {e}")


def check_lock_file(force=False):
    """Check if script already ran today. Returns True if should proceed."""
    today = datetime.date.today().isoformat()
    
    if LOCK_FILE.exists():
        try:
            with open(LOCK_FILE, "r") as f:
                lock_date = f.read().strip()
            if lock_date == today and not force:
                log_message(f"Lock file exists with today's date. Exiting (use --force to override)")
                return False
        except Exception as e:
            log_message(f"Error reading lock file: {e}")
    
    try:
        with open(LOCK_FILE, "w") as f:
            f.write(today)
        log_message("Lock file created/updated")
    except Exception as e:
        log_message(f"Error writing lock file: {e}")
    
    return True


def load_history():
    """Load story history from JSON file."""
    if not HISTORY_FILE.exists():
        log_message("History file not found, starting with empty history")
        return []
    
    try:
        with open(HISTORY_FILE, "r") as f:
            data = json.load(f)
            return data.get("stories", [])
    except Exception as e:
        log_message(f"Error loading history: {e}")
        return []


def save_history(stories):
    """Save stories to history JSON file."""
    try:
        data = {
            "_description": "Tracks story topics published in the last 7 days. Auto-updated by rws_daily_auto.py.",
            "stories": stories
        }
        with open(HISTORY_FILE, "w") as f:
            json.dump(data, f, indent=2)
        log_message(f"History saved with {len(stories)} entries")
    except Exception as e:
        log_message(f"Error saving history: {e}")


def get_recent_topics(days=7):
    """Get set of topic keywords from last N days."""
    stories = load_history()
    cutoff_date = datetime.date.today() - datetime.timedelta(days=days)
    recent_topics = set()
    
    for story in stories:
        try:
            story_date = datetime.date.fromisoformat(story.get("date", ""))
            if story_date >= cutoff_date:
                topic = story.get("topic", "")
                if topic:
                    recent_topics.add(topic)
        except Exception as e:
            log_message(f"Error parsing story date: {e}")
    
    log_message(f"Found {len(recent_topics)} recent topics in last {days} days")
    return recent_topics


def add_to_history(date_str, slug, topic):
    """Add new story to history and prune old entries."""
    stories = load_history()
    
    stories.append({
        "date": date_str,
        "slug": slug,
        "topic": topic
    })
    
    cutoff_date = datetime.date.today() - datetime.timedelta(days=14)
    stories = [
        s for s in stories 
        if datetime.date.fromisoformat(s.get("date", "")) >= cutoff_date
    ]
    
    save_history(stories)
    log_message(f"Added story to history: {slug}")


def select_story(recent_topics):
    """Call Anthropic API with live web search to select 10 story candidates for today.

    Uses web_search_20250305 so Claude actually searches for today's news
    rather than drawing from training data (which would produce stale 2025 stories).
    Returns a list of 10 story dicts. The user picks one by replying 1–10.
    """
    try:
        import anthropic
    except ImportError:
        log_message("Error: anthropic library not installed. Run: pip install anthropic")
        return None

    if not ENV.get("ANTHROPIC_API_KEY"):
        log_message("Error: ANTHROPIC_API_KEY not set in .env")
        return None

    today = datetime.date.today().isoformat()
    recent_topics_str = ", ".join(sorted(recent_topics)) if recent_topics else "None"

    system_prompt = f"""You are the story selector for Red White & Skewed, a political news site that covers stories with maximum partisan divide. TODAY IS {today}. You MUST use web_search to find today's real breaking news — do NOT use stories from your training data."""

    user_prompt = f"""TODAY IS {today}. Recent topics already covered (AVOID these): {recent_topics_str}.

STEP 1 — Search broadly across multiple issue areas. Run ALL of these searches:
- "US political news {today}"
- "breaking news politics today"
- "Congress White House news today"
- "Supreme Court ruling news today"
- "economy inflation jobs news today"
- "immigration border news today"
- "foreign policy military news today"
- "culture war education news today"

STEP 2 — From your search results, identify 10 stories with strong partisan divide happening RIGHT NOW (today or yesterday at the earliest). Each must be a story that conservatives and liberals are framing very differently.

MANDATORY DIVERSITY RULES — your 10 stories MUST span at least 6 different issue areas from this list:
1. Political investigations / legal / DOJ / courts
2. Economy / inflation / jobs / taxes / budget
3. Immigration / border / deportation
4. Foreign policy / military / national security
5. Culture / education / social issues / DEI
6. Environment / climate / energy
7. Healthcare / social programs
8. Congress / legislation / elections
9. Supreme Court / judiciary
10. Tech / AI / regulation / media

Do NOT pick multiple stories from the same issue area. Avoid topics already covered (listed above).

STEP 3 — Return ONLY a valid JSON array of exactly 10 story objects (no markdown, no explanation) with these exact keys per story:
[
  {{
    "title": "RWS-style headline framed as 'X or Y? Description'",
    "slug": "url-safe-filename-no-spaces",
    "topic_keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
    "conservative_headline": "How Fox News would frame this headline",
    "liberal_headline": "How MSNBC would frame this headline",
    "poll_question": "Short question about the core debate",
    "poll_option1_label": "Conservative label (1-3 words)",
    "poll_option1_desc": "Conservative position description (under 15 words)",
    "poll_option2_label": "Liberal label (1-3 words)",
    "poll_option2_desc": "Liberal position description (under 15 words)",
    "pexels_search_terms": "3-4 keywords for finding a relevant photo"
  }},
  ... 9 more stories ...
]"""

    try:
        client = anthropic.Anthropic(api_key=ENV["ANTHROPIC_API_KEY"])
        tools = [{"type": "web_search_20250305", "name": "web_search", "max_uses": 8}]
        messages = [{"role": "user", "content": user_prompt}]

        response_text = ""
        for iteration in range(12):
            response = client.messages.create(
                model="claude-opus-5",
                max_tokens=6000,
                system=system_prompt,
                tools=tools,
                messages=messages,
            )
            log_message(f"Story selection iteration {iteration + 1}: stop_reason={response.stop_reason}")

            if response.stop_reason == "end_turn":
                for block in response.content:
                    if hasattr(block, "text"):
                        response_text += block.text
                break
            elif response.stop_reason == "pause_turn":
                messages.append({"role": "assistant", "content": response.content})
            else:
                for block in response.content:
                    if hasattr(block, "text"):
                        response_text += block.text
                break

        if not response_text:
            log_message("Error: No text response from story selection")
            return None

        # Strip markdown fences if present
        response_text = re.sub(r'^```(?:json)?\s*', '', response_text.strip(), flags=re.MULTILINE)
        response_text = re.sub(r'\s*```$', '', response_text.strip(), flags=re.MULTILINE)

        # Find the JSON array [...] in the response
        array_match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if not array_match:
            log_message(f"Error: No JSON array found in story selection response: {response_text[:200]}")
            return None

        stories = json.loads(array_match.group())
        if not isinstance(stories, list) or len(stories) == 0:
            log_message(f"Error: Expected JSON array of stories, got: {type(stories)}")
            return None

        # Trim to exactly 10 if we got more
        stories = stories[:10]
        log_message(f"Stories selected: {len(stories)} candidates")
        for i, s in enumerate(stories, 1):
            log_message(f"  {i}. {s.get('slug', 'unknown')} — {s.get('title', '')[:60]}")
        return stories

    except json.JSONDecodeError as e:
        log_message(f"Error parsing story selection JSON: {e}")
        return None
    except Exception as e:
        log_message(f"Error calling Anthropic API for story selection: {e}")
        return None


def find_pexels_image(search_terms):
    """Find a Pexels image via Claude web_search (no API key required).

    The Pexels REST API is blocked from GitHub Actions IPs. Instead, we ask
    Claude to search for a relevant landscape photo on pexels.com and return
    the direct CDN URL, photographer, and page link.
    """
    if isinstance(search_terms, list):
        search_terms = " ".join(search_terms)
    search_terms = str(search_terms).strip()

    api_key = ENV.get("ANTHROPIC_API_KEY")
    if not api_key:
        log_message("Warning: ANTHROPIC_API_KEY not set, cannot search for image")
        return {"url": "", "page": "", "credit": "Image not available"}

    try:
        import anthropic, re as _re

        client = anthropic.Anthropic(api_key=api_key)
        tools = [{"type": "web_search_20250305", "name": "web_search", "max_uses": 4}]
        messages = [{
            "role": "user",
            "content": (
                f'Search pexels.com for a landscape photo about: "{search_terms}".\n\n'
                f'Run web_search with: site:pexels.com {search_terms}\n\n'
                f'From the results, find a Pexels photo page URL like:\n'
                f'  https://www.pexels.com/photo/some-title-here-1234567/\n'
                f'The number at the end (e.g. 1234567) is the photo ID. It must be greater than 500000.\n\n'
                f'Using the ACTUAL photo ID and ACTUAL photographer name you found, return ONLY this JSON:\n'
                f'{{"url":"https://images.pexels.com/photos/{{PHOTO_ID}}/pexels-photo-{{PHOTO_ID}}.jpeg?auto=compress&cs=tinysrgb&w=1200",'
                f'"page":"https://www.pexels.com/photo/{{SLUG}}-{{PHOTO_ID}}/",'
                f'"credit":"Photo: {{PHOTOGRAPHER_NAME}} / Pexels"}}\n\n'
                f'Replace {{PHOTO_ID}}, {{SLUG}}, and {{PHOTOGRAPHER_NAME}} with the REAL values from the search results.\n'
                f'No markdown fences. No explanation. Just the JSON.'
            )
        }]

        response_text = ""
        for _ in range(6):
            resp = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=512,
                tools=tools,
                messages=messages,
            )
            if resp.stop_reason == "end_turn":
                for block in resp.content:
                    if hasattr(block, "text"):
                        response_text += block.text
                break
            elif resp.stop_reason == "pause_turn":
                messages.append({"role": "assistant", "content": resp.content})
            else:
                break

        if response_text:
            # Extract JSON from response
            match = _re.search(r'\{[^{}]+\}', response_text, _re.DOTALL)
            if match:
                try:
                    result = json.loads(match.group())
                except json.JSONDecodeError:
                    result = {}
                url = result.get("url", "")
                # Reject template/placeholder URLs that Claude didn't fill in
                if (url and "pexels.com" in url
                        and "NNNNNN" not in url
                        and "/ID/" not in url
                        and "REAL_ID" not in url
                        and _re.search(r'/photos/\d+/', url)):
                    log_message(f"Image found via web search: {result.get('credit', '')} | URL: {url[:80]}")
                    return result
                elif url:
                    log_message(f"Warning: Image URL failed validation (template/invalid): {url[:80]}")

        log_message("Warning: Could not find Pexels image via web search")
        return {"url": "", "page": "", "credit": "Image not found"}

    except Exception as e:
        log_message(f"Error finding image via web search: {e}")
        return {"url": "", "page": "", "credit": "Image search failed"}


def send_story_email(stories):
    """Send HTML email with 10 numbered story options to jim@redwhiteandskewed.com.

    The user replies with the number (1–10) of the story they want published.
    """
    today = datetime.date.today().isoformat()

    smtp_host = ENV.get("SMTP_HOST", "send.one.com")
    smtp_port = int(ENV.get("SMTP_PORT", "465"))
    from_email = ENV.get("SMTP_FROM", "info@redwhiteandskewed.com")
    to_email = "jim@redwhiteandskewed.com"

    if not ENV.get("SMTP_PASSWORD"):
        log_message("Error: SMTP_PASSWORD not set in .env")
        return False

    subject = f"🗞️ RWS Story Choices — {today} — Reply 1–{len(stories)} to Publish"

    # Build numbered story cards
    stories_html = ""
    for i, story in enumerate(stories, 1):
        title = story.get("title", "")
        con_head = story.get("conservative_headline", "")
        lib_head = story.get("liberal_headline", "")
        bg_color = "#ffffff" if i % 2 == 0 else "#f9f9f9"
        stories_html += f"""
        <div style="background: {bg_color}; border: 1px solid #ddd; border-radius: 8px; padding: 16px; margin: 12px 0;">
            <p style="margin: 0 0 8px 0; font-size: 22px; font-weight: bold; color: #1a1a1a;">
                <span style="display: inline-block; background: #1a1a1a; color: white; border-radius: 50%; width: 32px; height: 32px; text-align: center; line-height: 32px; margin-right: 10px; font-size: 16px;">{i}</span>
                {title}
            </p>
            <p style="margin: 6px 0 4px 42px; color: #c0392b; font-size: 13px;">
                🔴 <strong>Right:</strong> {con_head}
            </p>
            <p style="margin: 4px 0 0 42px; color: #2980b9; font-size: 13px;">
                🔵 <strong>Left:</strong> {lib_head}
            </p>
        </div>"""

    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; background: #f4f4f4;">
        <div style="max-width: 700px; margin: 0 auto; padding: 20px;">
            <div style="text-align: center; margin-bottom: 24px; background: #1a1a1a; padding: 20px; border-radius: 10px;">
                <h1 style="color: white; margin: 0; font-size: 28px;">Red White &amp; Skewed</h1>
                <p style="color: #aaa; margin: 6px 0 0 0; font-size: 14px;">Daily Story Selection — {today}</p>
            </div>

            <div style="background: #fff3cd; border-left: 4px solid #f39c12; padding: 14px 18px; border-radius: 6px; margin-bottom: 20px;">
                <p style="margin: 0; font-size: 15px;">
                    <strong>Reply to this email with a number (1–{len(stories)})</strong> to publish that story today.
                    No reply by 9 AM tomorrow = story skipped.
                </p>
            </div>

            {stories_html}

            <div style="text-align: center; color: #999; font-size: 11px; margin-top: 24px; border-top: 1px solid #ddd; padding-top: 14px;">
                <p>Red White &amp; Skewed Daily Automation</p>
            </div>
        </div>
    </body>
    </html>
    """

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = from_email
        msg["To"] = to_email

        msg.attach(MIMEText(html_body, "html"))

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as server:
            server.login(from_email, ENV.get("SMTP_PASSWORD"))
            server.sendmail(from_email, to_email, msg.as_string())

        log_message(f"Story choice email sent to {to_email} with {len(stories)} options")
        return True

    except Exception as e:
        log_message(f"Error sending email: {e}")
        return False


def save_state(stories):
    """Save list of 10 story candidates to state/pending_story.json for reply_monitor.

    The reply_monitor reads this and uses the user's reply number (1–10) to look up
    which story was chosen, then generates and publishes only that one story.
    """
    today = datetime.date.today().isoformat()
    email_sent_at = datetime.datetime.now().isoformat()

    state = {
        "date": today,
        "email_sent_at": email_sent_at,
        "stories": stories,   # list of up to 10 story dicts
    }

    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
        log_message(f"State saved: {len(stories)} story candidates → {STATE_FILE}")
        return True
    except Exception as e:
        log_message(f"Error saving state: {e}")
        return False


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Red White & Skewed Daily Story Automation")
    parser.add_argument("--test-email", action="store_true", help="Send test email only")
    parser.add_argument("--force", action="store_true", help="Run even if already ran today")
    args = parser.parse_args()
    
    log_message("=" * 60)
    log_message("RWS Daily Story Automation Started")
    
    load_env()
    
    if args.test_email:
        log_message("Test email mode enabled")
        test_stories = [
            {
                "title": f"Test Story {i}: Policy Debate on Topic {i}",
                "slug": f"test-story-{i}",
                "topic_keywords": ["government", "policy", "test"],
                "conservative_headline": f"Conservative framing of story {i}",
                "liberal_headline": f"Liberal framing of story {i}",
                "poll_question": "Which side do you agree with?",
                "poll_option1_label": "Right",
                "poll_option1_desc": "Conservative position here",
                "poll_option2_label": "Left",
                "poll_option2_desc": "Liberal position here",
                "pexels_search_terms": "government politics news"
            }
            for i in range(1, 11)
        ]
        send_story_email(test_stories)
        log_message("Test email completed")
        return
    
    if not check_lock_file(force=args.force):
        log_message("Exiting: Script already ran today")
        return
    
    try:
        recent_topics = get_recent_topics(days=7)

        stories = select_story(recent_topics)
        if not stories:
            log_message("Error: Failed to select stories, aborting")
            return

        # No image search here — images are fetched only when the user picks a story
        # (in handle_option_1 → generate_full_story). This avoids wasting 10 image
        # searches for stories that will never be published.

        email_sent = send_story_email(stories)
        if not email_sent:
            log_message("Error: Failed to send email, aborting")
            return

        save_state(stories)

        log_message(f"Success: {len(stories)} story options emailed. Waiting for user reply (1–{len(stories)})...")
        
    except Exception as e:
        log_message(f"Unexpected error in main: {e}")
        import traceback
        log_message(traceback.format_exc())
    
    log_message("RWS Daily Story Automation Completed")
    log_message("=" * 60)


if __name__ == "__main__":
    main()
