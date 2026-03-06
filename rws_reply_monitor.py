#!/usr/bin/env python3
"""
Red White & Skewed — Email Reply Monitor
Checks jim@redwhiteandskewed.com for a reply to the daily story email.
Runs every 30 minutes via Mac cron job after the 10 PM selector runs.

Usage:
    python3 rws_reply_monitor.py           # Normal run
    python3 rws_reply_monitor.py --status  # Show current pending story status
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
import imaplib
import email
from email.header import decode_header as decode_email_header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib.request import urlopen, Request
from urllib.error import URLError
import time

SCRIPT_DIR = pathlib.Path(__file__).parent
HISTORY_FILE = SCRIPT_DIR / "story_history.json"
LOG_FILE = pathlib.Path("/tmp/rws_reply_monitor.log")
STATE_FILE = SCRIPT_DIR / "state" / "pending_story.json"

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
    """Call Anthropic API to select today's story."""
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
    
    system_prompt = f"""You are the story selector for Red White & Skewed, a political news site that covers stories with maximum partisan divide. Today is {today}. You must select a breaking news story and return a JSON object."""
    
    user_prompt = f"""Recent topics to AVOID (covered in last 7 days): {recent_topics_str}. Search for today's top US political news stories. Select the ONE story with the strongest partisan divide. Return ONLY a JSON object with these exact keys: title (the RWS-style 'X or Y? Description' headline), slug (url-safe filename), topic_keywords (5-8 keywords describing the topic), conservative_headline (how Fox News would frame it), liberal_headline (how MSNBC would frame it), poll_question (short question), poll_option1_label (conservative 1-3 word label), poll_option1_desc (under 15 words), poll_option2_label (liberal 1-3 word label), poll_option2_desc (under 15 words), pexels_search_terms (3-4 keywords to find a relevant image on pexels.com)"""
    
    try:
        client = anthropic.Anthropic(api_key=ENV["ANTHROPIC_API_KEY"])
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1024,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        
        response_text = response.content[0].text
        log_message(f"API response received: {len(response_text)} characters")
        
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if not json_match:
            log_message("Error: No JSON found in API response")
            return None
        
        story_data = json.loads(json_match.group())
        log_message(f"Story selected: {story_data.get('slug', 'unknown')}")
        return story_data
        
    except json.JSONDecodeError as e:
        log_message(f"Error parsing API response as JSON: {e}")
        return None
    except Exception as e:
        log_message(f"Error calling Anthropic API: {e}")
        return None


def find_pexels_image(search_terms, exclude_id=None):
    """Find image on Pexels API, optionally excluding a specific image ID."""
    # Normalize search_terms: Claude sometimes returns a list instead of a string
    if isinstance(search_terms, list):
        search_terms = " ".join(search_terms)
    search_terms = str(search_terms).strip()

    pexels_key = ENV.get("PEXELS_API_KEY")
    if not pexels_key:
        log_message("Warning: PEXELS_API_KEY not set, returning fallback image dict")
        return {
            "url": "",
            "page": "",
            "credit": "Image credit not available"
        }
    
    log_message(f"Pexels search: '{search_terms}' (key length: {len(pexels_key)}, ends with: {repr(pexels_key[-3:])})")
    try:
        from urllib.parse import urlencode
        from urllib.error import HTTPError
        params = urlencode({"query": search_terms, "per_page": 15, "orientation": "landscape"})
        url = f"https://api.pexels.com/v1/search?{params}"
        headers = {"Authorization": pexels_key}
        request = Request(url, headers=headers)

        with urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode())

        photos = data.get("photos", [])
        if not photos:
            log_message(f"No Pexels images found for: {search_terms}")
            return {
                "url": "",
                "page": "",
                "credit": "No image found"
            }

        selected_photo = None
        for photo in photos:
            photo_id = photo.get("id", 0)
            if exclude_id and photo_id == exclude_id:
                continue
            if photo_id > 500000:
                selected_photo = photo
                break

        if not selected_photo:
            for photo in photos:
                if not exclude_id or photo.get("id") != exclude_id:
                    selected_photo = photo
                    break

        if not selected_photo:
            selected_photo = photos[0]

        photo_id = selected_photo.get("id")
        photographer = selected_photo.get("photographer", "Unknown")
        photo_url = selected_photo.get("url", "")

        image_data = {
            "url": f"https://images.pexels.com/photos/{photo_id}/pexels-photo-{photo_id}.jpeg?auto=compress&cs=tinysrgb&w=1200",
            "page": photo_url,
            "credit": f"Photo: {photographer} / Pexels",
            "id": photo_id
        }
        log_message(f"Image found: {photo_id} by {photographer}")
        return image_data

    except HTTPError as e:
        log_message(f"Pexels API HTTP error: {e.code} {e.reason} — check PEXELS_API_KEY in GitHub Secrets")
        return {"url": "", "page": "", "credit": "Image fetch failed"}
    except URLError as e:
        log_message(f"Pexels network error: {e.reason} — check network connectivity")
        return {"url": "", "page": "", "credit": "Image fetch failed"}
    except Exception as e:
        log_message(f"Error in find_pexels_image: {e}")
        return {"url": "", "page": "", "credit": "Error fetching image"}


def find_image_via_search(search_terms):
    """Find a Pexels image via Claude Haiku web_search. Fast, standalone, no API key needed.

    Used in handle_option_1 so the image is always found regardless of whether
    the full story generation succeeds or fails.
    """
    if isinstance(search_terms, list):
        search_terms = " ".join(search_terms)
    search_terms = str(search_terms).strip()

    api_key = ENV.get("ANTHROPIC_API_KEY")
    if not api_key:
        log_message("Warning: No ANTHROPIC_API_KEY for image search")
        return {"url": "", "page": "", "credit": ""}

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        tools = [{"type": "web_search_20250305", "name": "web_search", "max_uses": 4}]
        messages = [{
            "role": "user",
            "content": (
                f'Search pexels.com for a landscape photo about: "{search_terms}". '
                f'Use web_search with query: site:pexels.com {search_terms}\n\n'
                f'Pick ONE photo with a numeric ID greater than 500000. '
                f'Return ONLY this JSON (no markdown, no explanation):\n'
                f'{{"url":"https://images.pexels.com/photos/ID/pexels-photo-ID.jpeg?auto=compress&cs=tinysrgb&w=1200",'
                f'"page":"https://www.pexels.com/photo/SLUG-ID/",'
                f'"credit":"Photo: Photographer Name / Pexels"}}'
            )
        }]

        response_text = ""
        for _ in range(6):
            resp = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=300,
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

        if response_text:
            match = re.search(r'\{[^{}]+\}', response_text, re.DOTALL)
            if match:
                result = json.loads(match.group())
                if result.get("url") and "pexels.com" in result.get("url", ""):
                    log_message(f"Image found: {result.get('credit', '')}")
                    return result

        log_message("Warning: Image search returned no usable result")
        return {"url": "", "page": "", "credit": ""}

    except Exception as e:
        log_message(f"Error in find_image_via_search: {e}")
        return {"url": "", "page": "", "credit": ""}


def decode_mime_header(header_str):
    """Decode MIME-encoded email headers (handles UTF-8/base64 encoded subjects with emoji)."""
    if not header_str:
        return ""
    try:
        parts = []
        for part, encoding in decode_email_header(header_str):
            if isinstance(part, bytes):
                parts.append(part.decode(encoding or "utf-8", errors="ignore"))
            else:
                parts.append(str(part))
        return "".join(parts)
    except Exception:
        return header_str  # fall back to raw string


def strip_html(html_string):
    """Remove HTML tags from string."""
    clean = re.compile('<.*?>')
    return re.sub(clean, '', html_string)


def extract_reply_option(email_body):
    """Extract reply option (1, 2, 3, or 4) from email body."""
    if not email_body:
        return None
    
    text = strip_html(email_body)
    
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
        words = line.split()
        if words and words[0] in ['1', '2', '3', '4']:
            try:
                return int(words[0])
            except ValueError:
                pass
    
    match = re.search(r'\b([1234])\b', text)
    if match:
        return int(match.group(1))
    
    return None


def send_story_email(story_data):
    """Send HTML email with story selection to jim@redwhiteandskewed.com."""
    today = datetime.date.today().isoformat()

    smtp_host = ENV.get("SMTP_HOST", "send.one.com")
    smtp_port = int(ENV.get("SMTP_PORT", "465"))
    from_email = ENV.get("SMTP_FROM", "info@redwhiteandskewed.com")
    to_email = "jim@redwhiteandskewed.com"

    if not ENV.get("SMTP_PASSWORD"):
        log_message("Error: SMTP_PASSWORD not set in .env")
        return False
    
    subject = f"🗞️ RWS Daily Story Pick — {today} — Action Required"
    
    image_url = story_data.get("image_url", "")
    image_html = ""
    if image_url:
        image_html = f'<div style="margin: 20px 0;"><img src="{image_url}" style="max-width:600px; border-radius: 8px;"></div>'
    
    conservative_headline = story_data.get("conservative_headline", "")
    liberal_headline = story_data.get("liberal_headline", "")
    poll_question = story_data.get("poll_question", "")
    poll_option1_label = story_data.get("poll_option1_label", "")
    poll_option1_desc = story_data.get("poll_option1_desc", "")
    poll_option2_label = story_data.get("poll_option2_label", "")
    poll_option2_desc = story_data.get("poll_option2_desc", "")
    title = story_data.get("title", "")
    
    poll_html = ""
    if poll_question:
        poll_html = f"""
        <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <p style="font-weight: bold; margin-bottom: 15px;">{poll_question}</p>
            <div style="display: flex; gap: 15px;">
                <div style="flex: 1; padding: 10px; background: white; border-left: 4px solid #e81b23; border-radius: 4px;">
                    <p style="margin: 0; font-weight: bold; color: #e81b23;">{poll_option1_label}</p>
                    <p style="margin: 5px 0 0 0; font-size: 12px;">{poll_option1_desc}</p>
                </div>
                <div style="flex: 1; padding: 10px; background: white; border-left: 4px solid #0066cc; border-radius: 4px;">
                    <p style="margin: 0; font-weight: bold; color: #0066cc;">{poll_option2_label}</p>
                    <p style="margin: 5px 0 0 0; font-size: 12px;">{poll_option2_desc}</p>
                </div>
            </div>
        </div>
        """
    
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 800px; margin: 0 auto; padding: 20px;">
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #1a1a1a; margin: 0;">Red White & Skewed</h1>
                <p style="color: #666; margin: 5px 0 0 0;">Daily Story Selection</p>
            </div>
            
            <div style="border-left: 4px solid #1a1a1a; padding-left: 20px; margin: 30px 0;">
                <h2 style="color: #1a1a1a; margin-top: 0;">{title}</h2>
            </div>
            
            {image_html}
            
            <div style="margin: 20px 0; padding: 15px; background: #fff3cd; border-left: 4px solid #e81b23; border-radius: 4px;">
                <p style="margin: 0; color: #d63031;"><strong>Conservative Take:</strong> {conservative_headline}</p>
            </div>
            
            <div style="margin: 20px 0; padding: 15px; background: #d1ecf1; border-left: 4px solid #0066cc; border-radius: 4px;">
                <p style="margin: 0; color: #0066cc;"><strong>Liberal Take:</strong> {liberal_headline}</p>
            </div>
            
            {poll_html}
            
            <div style="background: #f0f0f0; padding: 20px; border-radius: 8px; margin: 30px 0;">
                <h3 style="margin-top: 0; color: #1a1a1a;">Action Required</h3>
                <p style="margin: 10px 0;"><strong>Reply to this email with:</strong></p>
                <ul style="margin: 10px 0;">
                    <li><strong>1</strong> — Publish this story to redwhiteandskewed.com and Wix</li>
                    <li><strong>2</strong> — Pick a different story</li>
                    <li><strong>3</strong> — Keep story, find a different image</li>
                    <li><strong>4</strong> or no reply — Skip today, do nothing</li>
                </ul>
                <p style="color: #666; font-size: 12px; margin: 15px 0 0 0;">If you don't reply by 9 AM tomorrow, story will be skipped.</p>
            </div>
            
            <div style="text-align: center; color: #999; font-size: 11px; margin-top: 30px; border-top: 1px solid #ddd; padding-top: 15px;">
                <p>Red White & Skewed Daily Automation</p>
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

        log_message(f"Email sent successfully to {to_email}")
        return True

    except Exception as e:
        log_message(f"Error sending email: {e}")
        return False


def send_simple_email(to_email, subject, body):
    """Send simple text/html email."""
    smtp_host = ENV.get("SMTP_HOST", "send.one.com")
    smtp_port = int(ENV.get("SMTP_PORT", "465"))
    from_email = ENV.get("SMTP_FROM", "info@redwhiteandskewed.com")

    if not ENV.get("SMTP_PASSWORD"):
        log_message("Error: SMTP_PASSWORD not set in .env")
        return False
    
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = from_email
        msg["To"] = to_email
        
        is_html = "<" in body and ">" in body
        msg.attach(MIMEText(body, "html" if is_html else "plain"))
        
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as server:
            server.login(from_email, ENV.get("SMTP_PASSWORD"))
            server.sendmail(from_email, to_email, msg.as_string())

        log_message(f"Confirmation email sent to {to_email}")
        return True

    except Exception as e:
        log_message(f"Error sending confirmation email: {e}")
        return False


def load_pending_state():
    """Load pending story state from temp file."""
    if not STATE_FILE.exists():
        return None
    
    try:
        with open(STATE_FILE, "r") as f:
            state = json.load(f)
        log_message(f"Loaded pending state")
        return state
    except Exception as e:
        log_message(f"Error loading state: {e}")
        return None


def clear_pending_state():
    """Delete pending story state file."""
    if STATE_FILE.exists():
        try:
            STATE_FILE.unlink()
            log_message("Cleared pending state")
        except Exception as e:
            log_message(f"Error clearing state: {e}")


def save_pending_state(story_filename, story_data, image_data):
    """Save pending story state to temp file."""
    today = datetime.date.today().isoformat()
    email_sent_at = datetime.datetime.now().isoformat()
    
    state = {
        "story_filename": story_filename,
        "story_data": story_data,
        "image": image_data,
        "email_sent_at": email_sent_at,
        "date": today,
        "action_taken": False
    }
    
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
        log_message(f"State saved to {STATE_FILE}")
        return True
    except Exception as e:
        log_message(f"Error saving state: {e}")
        return False


def check_story_timeout(email_sent_at_str):
    """Check if story email was sent >11 hours ago (past 9 AM)."""
    try:
        email_sent_at = datetime.datetime.fromisoformat(email_sent_at_str)
        current_time = datetime.datetime.now()
        hours_elapsed = (current_time - email_sent_at).total_seconds() / 3600
        
        if hours_elapsed > 11:
            log_message(f"Story timeout: {hours_elapsed:.1f} hours elapsed since email sent")
            return True
        return False
    except Exception as e:
        log_message(f"Error checking story timeout: {e}")
        return False


def check_imap_for_reply():
    """Check IMAP inbox for reply to story email."""
    imap_host = ENV.get("IMAP_HOST", "imap.one.com")
    imap_port = int(ENV.get("IMAP_PORT", "993"))
    email_user = ENV.get("IMAP_USER", "jim@redwhiteandskewed.com")
    email_password = ENV.get("IMAP_PASSWORD")

    if not email_password:
        log_message("Error: IMAP_PASSWORD not set in .env")
        return None
    
    try:
        log_message(f"Connecting to IMAP server {imap_host}...")
        imap = imaplib.IMAP4_SSL(imap_host, imap_port, timeout=10)
        imap.login(email_user, email_password)
        log_message("IMAP login successful")
        
        imap.select("INBOX")
        log_message("Selected INBOX")
        
        status, messages = imap.search(None, "UNSEEN")
        if status != "OK":
            log_message("Error searching for unseen emails")
            imap.close()
            imap.logout()
            return None
        
        email_ids = messages[0].split()
        log_message(f"Found {len(email_ids)} unread emails")
        
        for email_id in reversed(email_ids):
            status, msg_data = imap.fetch(email_id, "(RFC822)")
            if status != "OK":
                log_message(f"Warning: fetch failed for email id={email_id!r}, status={status!r}")
                continue

            try:
                msg = email.message_from_bytes(msg_data[0][1])
                subject_raw = msg.get("Subject", "")
                subject = decode_mime_header(subject_raw)
                from_addr = msg.get("From", "")

                log_message(f"Checking email — subject: {subject!r} | from: {from_addr}")

                if "rws daily story pick" not in subject.lower():
                    continue

                log_message(f"Found reply from {from_addr}: {subject}")
                
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode(errors='ignore')
                            break
                        elif part.get_content_type() == "text/html":
                            body = part.get_payload(decode=True).decode(errors='ignore')
                else:
                    body = msg.get_payload(decode=True).decode(errors='ignore')
                
                option = extract_reply_option(body)
                log_message(f"Extracted option: {option}")
                
                imap.store(email_id, "+FLAGS", "\\Seen")
                log_message(f"Marked email as read")
                
                imap.close()
                imap.logout()
                
                return {
                    "option": option,
                    "subject": subject,
                    "from": from_addr,
                    "body": body
                }
            
            except Exception as e:
                log_message(f"Error processing email: {e}")
                continue
        
        log_message("No reply found")
        imap.close()
        imap.logout()
        return None
        
    except Exception as e:
        log_message(f"IMAP connection error: {e}")
        return None


def generate_full_story(story_data):
    """Call Claude API with live web search to write a complete RWS-style story.

    Uses the web_search_20250305 tool so Claude can find real partisan coverage
    from Fox News, MSNBC, etc. and quote actual statements before writing the story.
    Runs an agentic loop: each time Claude searches the web, the API returns
    stop_reason='pause_turn'; we add the response to messages and continue until
    stop_reason='end_turn'.
    """
    try:
        import anthropic
    except ImportError:
        log_message("Error: anthropic library not installed")
        return None

    if not ENV.get("ANTHROPIC_API_KEY"):
        log_message("Error: ANTHROPIC_API_KEY not set")
        return None

    today = datetime.date.today().isoformat()
    title = story_data.get("title", "")
    conservative_headline = story_data.get("conservative_headline", "")
    liberal_headline = story_data.get("liberal_headline", "")
    topic_keywords = story_data.get("topic_keywords", [])
    if isinstance(topic_keywords, list):
        topic_str = ", ".join(topic_keywords)
    else:
        topic_str = str(topic_keywords)

    # Read the full RWS style prompt from repo
    style_guide = ""
    prompt_path = SCRIPT_DIR / "rws_story_prompt.md"
    if prompt_path.exists():
        try:
            with open(prompt_path, "r") as f:
                style_guide = f.read()
            log_message(f"Loaded rws_story_prompt.md ({len(style_guide)} chars)")
        except Exception as e:
            log_message(f"Warning: Could not read rws_story_prompt.md: {e}")

    system_prompt = f"""You are the automated story writer for Red White & Skewed (RWS).

RWS presents each political story from three perspectives: Conservative, Liberal, and Fact Check — showing how each side's media ecosystem frames the same event for their audience.

TODAY'S DATE: {today}

RWS STYLE GUIDE:
{style_guide if style_guide else "Write passionate, partisan content that authentically captures each side's media framing."}"""

    # PHASE 1: Force a dedicated research turn with web search
    research_prompt = f"""I need you to research this political story for our RWS publication. TODAY IS {today}.

STORY TITLE: {title}
CONSERVATIVE HEADLINE: {conservative_headline}
LIBERAL HEADLINE: {liberal_headline}
TOPIC KEYWORDS: {topic_str}

YOUR JOB RIGHT NOW IS RESEARCH ONLY — no writing yet.

Use web_search to find:
1. How Fox News, Washington Examiner, Daily Wire, or other conservative outlets are covering this story
2. How MSNBC, The Guardian, Salon, or other liberal outlets are covering this story
3. Real quotes from named conservative commentators, politicians, or pundits about this topic
4. Real quotes from named liberal commentators, politicians, or pundits about this topic
5. Neutral facts from AP, Reuters, or similar outlets

Run at least 5-7 searches before summarizing. Suggested searches:
- "{topic_str} Fox News"
- "{topic_str} MSNBC"
- "{topic_str} Washington Examiner"
- "{topic_str} site:foxnews.com OR site:dailywire.com"
- "{topic_str} site:msnbc.com OR site:theguardian.com"
- "{topic_str} AP OR Reuters"
- "site:pexels.com {topic_str} photo" (to find a relevant landscape photo for the story)

For the Pexels image search: look for a landscape photo on pexels.com that visually represents this story topic. From the search results, find a direct Pexels photo URL in the format https://images.pexels.com/photos/NNNNNN/... and note the photo ID, photographer name, and Pexels page URL.

After searching, summarize what you found: list the key quotes, the framing each side is using, the actual article URLs you found, AND the Pexels image details (photo ID, direct image URL, photographer, page URL). Do NOT write the story JSON yet — just report your research findings."""

    write_prompt = f"""Great. Now use what you just found to write the full RWS story JSON.

CRITICAL FORMAT RULES:
- Output ONLY a valid JSON object. No markdown fences (no ```json), no explanation before or after.
- Use double quotes throughout — this must be valid JSON, not a Python dict.
- 6-9 paragraphs per section. First AND last paragraph wrapped in <strong>.
- Embed inline links using actual article URLs from your research — not just outlet homepages.
- Conservative link class: text-red-700 underline hover:text-red-900
- Liberal link class: text-blue-700 underline hover:text-blue-900
- Factcheck link class: text-purple-700 underline hover:text-purple-900
- All links: target="_blank" rel="noopener noreferrer"
- NO byline field in factcheck section.
- Sources: {{"text": "Outlet — article description", "url": "https://actual-article-url/"}}

Required JSON structure:
{{
  "subtitle": "One neutral sentence summarizing what happened",
  "image": {{
    "url": "https://images.pexels.com/photos/NNNNNN/pexels-photo-NNNNNN.jpeg?auto=compress&cs=tinysrgb&w=1200",
    "page": "https://www.pexels.com/photo/description-NNNNNN/",
    "credit": "Photo: Photographer Name / Pexels"
  }},
  "conservative": {{
    "headline": "{conservative_headline}",
    "byline": "As seen on Fox News, [Outlet2], [Outlet3]",
    "paragraphs": [
      "<strong>Bold opening in conservative voice.</strong>",
      "Paragraph with real quote inline: As <a href=\\"https://actual-url/\\" target=\\"_blank\\" rel=\\"noopener noreferrer\\" class=\\"text-red-700 underline hover:text-red-900\\">Fox News reported</a>, [actual quote or finding].",
      "... 4-7 more paragraphs making the conservative case with linked sources ...",
      "<strong>Bold closing paragraph.</strong>"
    ],
    "sources": [
      {{"text": "Fox News — Article title", "url": "https://foxnews.com/actual-article"}},
      {{"text": "Washington Examiner — Article title", "url": "https://washingtonexaminer.com/actual-article"}}
    ]
  }},
  "liberal": {{
    "headline": "{liberal_headline}",
    "byline": "As seen on MSNBC, [Outlet2], [Outlet3]",
    "paragraphs": [
      "<strong>Bold opening in progressive voice.</strong>",
      "Paragraph with real quote inline: <a href=\\"https://actual-url/\\" target=\\"_blank\\" rel=\\"noopener noreferrer\\" class=\\"text-blue-700 underline hover:text-blue-900\\">MSNBC</a> noted that [actual quote or finding].",
      "... 4-7 more paragraphs making the liberal case with linked sources ...",
      "<strong>Bold closing paragraph.</strong>"
    ],
    "sources": [
      {{"text": "MSNBC — Article title", "url": "https://msnbc.com/actual-article"}},
      {{"text": "The Guardian — Article title", "url": "https://theguardian.com/actual-article"}}
    ]
  }},
  "factcheck": {{
    "headline": "Separating Fact from Spin",
    "paragraphs": [
      "<strong>Both sides are presenting selective versions of events. Here is what we actually know.</strong>",
      "<p class=\\"text-xl font-bold text-purple-900\\">THE UNDISPUTED FACTS:</p>",
      "✓ <strong>Verified fact:</strong> Description with <a href=\\"https://actual-url/\\" target=\\"_blank\\" rel=\\"noopener noreferrer\\" class=\\"text-purple-700 underline hover:text-purple-900\\">sourced link</a>.",
      "✓ <strong>Second verified fact:</strong> Description with sourced link.",
      "<p class=\\"text-xl font-bold text-purple-900 mt-6\\">CONSERVATIVE SPIN VS. REALITY:</p>",
      "⚠️ <strong>Claim:</strong> Specific conservative claim — reality check.",
      "✓ <strong>Fair Point:</strong> What conservatives get right.",
      "<p class=\\"text-xl font-bold text-purple-900 mt-6\\">LIBERAL SPIN VS. REALITY:</p>",
      "⚠️ <strong>Claim:</strong> Specific liberal claim — reality check.",
      "✓ <strong>Fair Point:</strong> What liberals get right.",
      "<p class=\\"text-xl font-bold text-purple-900 mt-6\\">THE BIGGER PICTURE:</p>",
      "What both sides are missing or oversimplifying.",
      "<strong>The Bottom Line: Honest assessment without partisan spin.</strong>"
    ],
    "sources": [
      {{"text": "Associated Press — Article title", "url": "https://apnews.com/actual-article"}},
      {{"text": "Reuters — Article title", "url": "https://reuters.com/actual-article"}}
    ]
  }}
}}

Output the JSON now. Remember: valid JSON only, double quotes, no markdown fences."""

    def extract_json(text):
        """Robustly extract and parse JSON from a response string."""
        # Strip markdown fences
        text = re.sub(r'^```(?:json)?\s*', '', text.strip(), flags=re.MULTILINE)
        text = re.sub(r'\s*```$', '', text.strip(), flags=re.MULTILINE)

        # Try direct parse first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try to find the outermost {...} block
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            candidate = json_match.group()
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass
            # Last resort: Python literal eval for single-quoted dicts
            try:
                import ast
                result = ast.literal_eval(candidate)
                if isinstance(result, dict):
                    return result
            except Exception:
                pass

        log_message(f"JSON extraction failed. Response preview: {text[:400]}")
        return None

    try:
        client = anthropic.Anthropic(api_key=ENV["ANTHROPIC_API_KEY"])
        tools = [{"type": "web_search_20250305", "name": "web_search", "max_uses": 15}]

        # --- PHASE 1: Research turn (forces web search) ---
        log_message("Phase 1: Starting web research...")
        messages = [{"role": "user", "content": research_prompt}]
        research_text = ""
        max_iterations = 20

        for iteration in range(max_iterations):
            response = client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=4096,
                system=system_prompt,
                tools=tools,
                messages=messages,
            )
            log_message(f"Research iteration {iteration + 1}: stop_reason={response.stop_reason}, blocks={len(response.content)}")

            if response.stop_reason == "end_turn":
                for block in response.content:
                    if hasattr(block, "text"):
                        research_text += block.text
                log_message(f"Research complete: {len(research_text)} chars of findings")
                break
            elif response.stop_reason == "pause_turn":
                messages.append({"role": "assistant", "content": response.content})
                log_message(f"Web search in progress (iteration {iteration + 1})...")
            else:
                log_message(f"Unexpected stop_reason in research: {response.stop_reason}")
                for block in response.content:
                    if hasattr(block, "text"):
                        research_text += block.text
                break

        if not research_text:
            log_message("Warning: No research findings — proceeding with write phase anyway")

        # --- PHASE 2: Write turn (uses research findings, produces JSON) ---
        log_message("Phase 2: Writing story JSON from research...")
        write_messages = [
            {"role": "user", "content": research_prompt},
            {"role": "assistant", "content": research_text or "I searched but could not find specific recent coverage. I will write based on general knowledge of how each side frames this topic."},
            {"role": "user", "content": write_prompt},
        ]

        response_text = ""
        for iteration in range(5):  # Write phase rarely needs more than 1-2 turns
            response = client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=8192,
                system=system_prompt,
                tools=tools,
                messages=write_messages,
            )
            log_message(f"Write iteration {iteration + 1}: stop_reason={response.stop_reason}, blocks={len(response.content)}")

            if response.stop_reason == "end_turn":
                for block in response.content:
                    if hasattr(block, "text"):
                        response_text += block.text
                log_message(f"Write phase complete: {len(response_text)} chars")
                break
            elif response.stop_reason == "pause_turn":
                write_messages.append({"role": "assistant", "content": response.content})
                log_message(f"Additional search in write phase (iteration {iteration + 1})...")
            else:
                log_message(f"Unexpected stop_reason in write phase: {response.stop_reason}")
                for block in response.content:
                    if hasattr(block, "text"):
                        response_text += block.text
                break

        if not response_text:
            log_message("Error: No text response from write phase")
            return None

        content = extract_json(response_text)
        if content is None:
            log_message("Error: Could not extract valid JSON from story response")
            return None

        log_message("Full story content generated successfully with live web search")
        return content

    except Exception as e:
        log_message(f"Error generating full story: {e}")
        return None


def save_story_json(story_data, image_data, full_content=None):
    """Save complete story JSON file and return filename."""
    today = datetime.date.today().isoformat()
    slug = story_data.get("slug", "story")
    filename = f"{today}-{slug}.json"
    filepath = SCRIPT_DIR / filename

    # Use full content if available, otherwise fall back to headlines only
    conservative = full_content.get("conservative") if full_content else None
    liberal = full_content.get("liberal") if full_content else None
    factcheck = full_content.get("factcheck") if full_content else None

    # Prefer image from Claude's web-searched full_content; fall back to Pexels API image_data
    ai_image = full_content.get("image", {}) if full_content else {}
    resolved_image_url    = ai_image.get("url", "")    or image_data.get("url", "")
    resolved_image_credit = ai_image.get("credit", "") or image_data.get("credit", "Photo: Pexels")
    resolved_image_page   = ai_image.get("page", "")   or image_data.get("page", "")

    story_json = {
        "date": today,
        "title": story_data.get("title", ""),
        "subtitle": full_content.get("subtitle", "") if full_content else "",
        "image": {
            "url": resolved_image_url,
            "credit": resolved_image_credit,
            "alt": story_data.get("title", ""),
            "source": "Pexels",
            "page": resolved_image_page,
            "license": "Pexels License"
        },
        "poll": {
            "question": story_data.get("poll_question", ""),
            "options": [
                {
                    "label": story_data.get("poll_option1_label", ""),
                    "description": story_data.get("poll_option1_desc", "")
                },
                {
                    "label": story_data.get("poll_option2_label", ""),
                    "description": story_data.get("poll_option2_desc", "")
                }
            ]
        },
        "conservative": conservative or {
            "headline": story_data.get("conservative_headline", ""),
            "byline": "From the Right",
            "paragraphs": [],
            "sources": []
        },
        "liberal": liberal or {
            "headline": story_data.get("liberal_headline", ""),
            "byline": "From the Left",
            "paragraphs": [],
            "sources": []
        },
        "factcheck": factcheck or {
            "headline": "Just the Facts",
            "byline": "Fact Check Desk",
            "paragraphs": [],
            "sources": []
        }
    }

    try:
        with open(filepath, "w") as f:
            json.dump(story_json, f, indent=2)
        log_message(f"Story JSON saved: {filename}")
        return filename
    except Exception as e:
        log_message(f"Error saving story JSON: {e}")
        return None


def publish_story(story_filename):
    """Publish story to one.com (SFTP) and Wix. Bypasses rws_publish.sh which requires .env."""
    try:
        story_path = SCRIPT_DIR / story_filename
        if not story_path.exists():
            log_message(f"Error: Story file not found: {story_path}")
            return False

        # Step 1: Upload to one.com via rws_upload.py (reads SFTP creds from env vars)
        log_message(f"Uploading to one.com: {story_filename}...")
        result = subprocess.run(
            ["python3", "rws_upload.py", "--story", str(story_path)],
            cwd=str(SCRIPT_DIR),
            capture_output=True,
            timeout=60,
            env={**os.environ}  # Pass all env vars (includes SFTP creds from GitHub Actions)
        )
        log_message(f"rws_upload.py stdout: {result.stdout.decode().strip()}")
        if result.returncode != 0:
            log_message(f"rws_upload.py failed: {result.stderr.decode().strip()}")
            return False
        log_message("one.com upload completed successfully")

        # Step 2: Publish to Wix via rws_to_wix.py (reads Wix creds from env vars)
        log_message(f"Publishing to Wix: {story_filename}...")
        result = subprocess.run(
            ["python3", "rws_to_wix.py", str(story_path)],
            cwd=str(SCRIPT_DIR),
            capture_output=True,
            timeout=60,
            env={**os.environ}
        )
        log_message(f"rws_to_wix.py stdout: {result.stdout.decode().strip()}")
        if result.returncode != 0:
            log_message(f"rws_to_wix.py failed: {result.stderr.decode().strip()}")
            return False
        log_message("Wix publish completed successfully")

        return True

    except subprocess.TimeoutExpired:
        log_message("Error: Publishing scripts timed out after 60s")
        return False
    except Exception as e:
        log_message(f"Error publishing story: {e}")
        return False


def handle_option_1(state):
    """OPTION 1: Publish story."""
    log_message("User chose option 1: PUBLISH")

    # Handle both state formats:
    # - rws_daily_auto.py saves: {"story": {...}, "image": {...}}
    # - rws_reply_monitor.py saves: {"story_data": {...}, "story_filename": "...", "image": {...}}
    story_data = state.get("story_data") or state.get("story")
    story_filename = state.get("story_filename")
    image_data = state.get("image", {})

    if not story_data:
        log_message("Error: Missing story data for publish")
        return False

    # Step 1: Find image first (fast, independent of story generation)
    # Use existing image from state if it has a URL; otherwise search for one now
    if not image_data.get("url"):
        log_message("No image in state — searching for one via web...")
        search_terms = story_data.get("pexels_search_terms") or story_data.get("topic_keywords", "news politics")
        image_data = find_image_via_search(search_terms)
        log_message(f"Image search result: {image_data.get('url', 'none')[:80]}")
    else:
        log_message(f"Using image from state: {image_data.get('url','')[:80]}")

    # Step 2: Generate full article content (conservative/liberal/factcheck) via Claude API
    log_message("Generating full article content via Claude API...")
    full_content = generate_full_story(story_data)
    if full_content:
        log_message("Full article content generated successfully")
        # If generate_full_story also found an image, prefer it (more relevant)
        ai_image = full_content.get("image", {})
        if ai_image.get("url"):
            image_data = ai_image
            log_message(f"Using image from story generation: {image_data['url'][:80]}")
    else:
        log_message("Warning: Could not generate full content — publishing with headlines only")

    # Step 3: Save complete story JSON (with full content if available)
    if not story_filename:
        story_filename = save_story_json(story_data, image_data, full_content)
        if not story_filename:
            log_message("Error: Failed to save story JSON")
            return False
    else:
        # Story file already exists — update it with the full content and image
        story_path = SCRIPT_DIR / story_filename
        try:
            with open(story_path, "r") as f:
                existing = json.load(f)
            # Always update image (was empty before)
            if image_data.get("url"):
                existing["image"] = {
                    "url": image_data.get("url", ""),
                    "credit": image_data.get("credit", "Photo: Pexels"),
                    "alt": story_data.get("title", ""),
                    "source": "Pexels",
                    "page": image_data.get("page", ""),
                    "license": "Pexels License"
                }
            if full_content:
                existing["subtitle"] = full_content.get("subtitle", existing.get("subtitle", ""))
                existing["conservative"] = full_content.get("conservative", existing.get("conservative", {}))
                existing["liberal"] = full_content.get("liberal", existing.get("liberal", {}))
                existing["factcheck"] = full_content.get("factcheck", {})
            with open(story_path, "w") as f:
                json.dump(existing, f, indent=2)
            log_message(f"Updated existing story JSON with full content and image")
        except Exception as e:
            log_message(f"Warning: Could not update existing story file: {e}")

    if not publish_story(story_filename):
        log_message("Error: Failed to publish story")
        return False
    
    topic = " ".join(story_data.get("topic_keywords", []))
    slug = story_data.get("slug", "")
    today = datetime.date.today().isoformat()
    
    add_to_history(today, slug, topic)
    
    # image_data is already fully resolved above (search ran if it was empty)
    pub_image_url    = image_data.get("url", "")    if image_data else ""
    pub_image_credit = image_data.get("credit", "") if image_data else ""
    pub_image_html = ""
    if pub_image_url:
        pub_image_html = f"""
        <div style="margin: 20px 0;">
            <img src="{pub_image_url}" style="max-width: 600px; width: 100%; border-radius: 8px;" alt="{story_data.get('title', '')}">
            <p style="font-size: 11px; color: #999; margin: 4px 0 0 0;">{pub_image_credit}</p>
        </div>"""

    send_simple_email(
        "jim@redwhiteandskewed.com",
        "✅ Story Published!",
        f"""<html><body style="font-family: Arial, sans-serif; max-width: 640px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #1a1a1a;">Story Published!</h2>
        <p><strong>{story_data.get('title', '')}</strong></p>
        {pub_image_html}
        <p><a href="https://redwhiteandskewed.com" style="color: #0066cc;">View on Red White &amp; Skewed →</a></p>
        </body></html>"""
    )
    
    clear_pending_state()
    log_message("Option 1 completed successfully")
    return True


def handle_option_2(state):
    """OPTION 2: Select new story."""
    log_message("User chose option 2: NEW STORY")

    story_data = state.get("story_data") or state.get("story")
    recent_topics = get_recent_topics(days=7)
    
    if story_data:
        pending_topic = " ".join(story_data.get("topic_keywords", []))
        recent_topics.add(pending_topic)
    
    new_story = select_story(recent_topics)
    if not new_story:
        log_message("Error: Failed to select new story")
        return False
    
    pexels_search = new_story.get("pexels_search_terms", "news politics")
    image_data = find_pexels_image(pexels_search)
    
    new_story["image_url"] = image_data.get("url", "")
    new_story["image_page"] = image_data.get("page", "")
    new_story["image_credit"] = image_data.get("credit", "")
    
    story_filename = save_story_json(new_story, image_data)
    if not story_filename:
        log_message("Error: Failed to save story JSON")
        return False
    
    send_story_email(new_story)
    
    save_pending_state(story_filename, new_story, image_data)
    
    log_message("Option 2 completed successfully")
    return True


def handle_option_3(state):
    """OPTION 3: New image only."""
    log_message("User chose option 3: NEW IMAGE")

    story_data = state.get("story_data") or state.get("story")
    story_filename = state.get("story_filename")
    current_image = state.get("image", {})
    
    if not story_filename or not story_data:
        log_message("Error: Missing story data")
        return False
    
    current_image_id = current_image.get("id")
    pexels_search = story_data.get("pexels_search_terms", "news politics")
    
    image_data = find_pexels_image(pexels_search, exclude_id=current_image_id)
    
    story_data["image_url"] = image_data.get("url", "")
    story_data["image_page"] = image_data.get("page", "")
    story_data["image_credit"] = image_data.get("credit", "")
    
    try:
        story_path = SCRIPT_DIR / story_filename
        with open(story_path, "r") as f:
            story_json = json.load(f)
        
        story_json["image"] = {
            "url": image_data.get("url", ""),
            "credit": image_data.get("credit", ""),
            "alt": story_json.get("image", {}).get("alt", ""),
            "source": "Pexels",
            "page": image_data.get("page", ""),
            "license": "Pexels License"
        }
        
        with open(story_path, "w") as f:
            json.dump(story_json, f, indent=2)
        
        log_message(f"Updated story JSON with new image: {story_filename}")
    except Exception as e:
        log_message(f"Error updating story JSON: {e}")
        return False
    
    send_story_email(story_data)
    
    save_pending_state(story_filename, story_data, image_data)
    
    log_message("Option 3 completed successfully")
    return True


def handle_option_4(state):
    """OPTION 4: Skip story."""
    log_message("User chose option 4 or no reply: SKIP")
    
    send_simple_email(
        "jim@redwhiteandskewed.com",
        "Skipped",
        "<html><body><p>Today's story has been skipped.</p></body></html>"
    )
    
    clear_pending_state()
    log_message("Option 4 completed successfully")
    return True


def show_status():
    """Show current pending story status."""
    state = load_pending_state()
    
    if not state:
        print("No pending story currently.")
        return
    
    print("Current Pending Story:")
    print(f"  Date: {state.get('date')}")
    print(f"  File: {state.get('story_filename')}")
    print(f"  Title: {state.get('story_data', {}).get('title', 'Unknown')}")
    print(f"  Email sent at: {state.get('email_sent_at')}")
    
    email_sent_at = state.get("email_sent_at")
    if email_sent_at and check_story_timeout(email_sent_at):
        print("  Status: TIMEOUT (past 9 AM, will be skipped)")
    else:
        print("  Status: Waiting for reply")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Red White & Skewed Email Reply Monitor")
    parser.add_argument("--status", action="store_true", help="Show current pending story status")
    args = parser.parse_args()
    
    log_message("=" * 60)
    log_message("RWS Reply Monitor Started")
    
    load_env()
    
    if args.status:
        show_status()
        return
    
    try:
        state = load_pending_state()
        
        if not state:
            log_message("No pending story, exiting silently")
            return
        
        email_sent_at = state.get("email_sent_at")
        if email_sent_at and check_story_timeout(email_sent_at):
            log_message("Story timeout: email sent >11 hours ago, skipping")
            clear_pending_state()
            return
        
        reply = check_imap_for_reply()
        
        if not reply:
            log_message("No reply received yet, continuing to wait")
            return
        
        option = reply.get("option")
        
        if option is None:
            log_message("Could not extract valid option from reply")
            return
        
        if option == 1:
            handle_option_1(state)
        elif option == 2:
            handle_option_2(state)
        elif option == 3:
            handle_option_3(state)
        elif option == 4:
            handle_option_4(state)
        else:
            log_message(f"Invalid option: {option}")
        
    except Exception as e:
        log_message(f"Unexpected error in main: {e}")
        import traceback
        log_message(traceback.format_exc())
    
    log_message("RWS Reply Monitor Completed")
    log_message("=" * 60)


if __name__ == "__main__":
    main()
