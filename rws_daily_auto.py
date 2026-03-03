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
            ENV[key] = val

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


def find_pexels_image(search_terms):
    """Find image on Pexels API."""
    pexels_key = ENV.get("PEXELS_API_KEY")
    if not pexels_key:
        log_message("Warning: PEXELS_API_KEY not set, returning fallback image dict")
        return {
            "url": "",
            "page": "",
            "credit": "Image credit not available"
        }
    
    try:
        url = f"https://api.pexels.com/v1/search?query={search_terms}&per_page=5&orientation=landscape"
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
            if photo.get("id", 0) > 500000:
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
            "credit": f"Photo: {photographer} / Pexels"
        }
        log_message(f"Image found: {photo_id} by {photographer}")
        return image_data
        
    except URLError as e:
        log_message(f"Error fetching from Pexels: {e}")
        return {
            "url": "",
            "page": "",
            "credit": "Image fetch failed"
        }
    except Exception as e:
        log_message(f"Error in find_pexels_image: {e}")
        return {
            "url": "",
            "page": "",
            "credit": "Error fetching image"
        }


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


def save_state(story_data, image_data):
    """Save pending story state to state/pending_story.json for reply_monitor."""
    today = datetime.date.today().isoformat()
    email_sent_at = datetime.datetime.now().isoformat()

    state = {
        "date": today,
        "email_sent_at": email_sent_at,
        "story": story_data,
        "image": image_data
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
        test_story = {
            "title": "Policy Debate: Should Federal Government Expand or Limit?",
            "slug": "test-story",
            "topic_keywords": ["government", "policy", "expansion", "federal"],
            "conservative_headline": "Government overreach threatens American freedoms and the free market",
            "liberal_headline": "Stronger government action needed to address inequality and protect citizens",
            "poll_question": "Which approach do you prefer?",
            "poll_option1_label": "Limited Gov",
            "poll_option1_desc": "Less federal intervention, more state/local control",
            "poll_option2_label": "Strong Gov",
            "poll_option2_desc": "More federal programs and regulations",
            "pexels_search_terms": "government building politics",
            "image_url": "",
            "image_page": "",
            "image_credit": "Test image"
        }
        send_story_email(test_story)
        log_message("Test email completed")
        return
    
    if not check_lock_file(force=args.force):
        log_message("Exiting: Script already ran today")
        return
    
    try:
        recent_topics = get_recent_topics(days=7)
        
        story_data = select_story(recent_topics)
        if not story_data:
            log_message("Error: Failed to select story, aborting")
            return
        
        pexels_search = story_data.get("pexels_search_terms", "news politics")
        image_data = find_pexels_image(pexels_search)
        
        story_data["image_url"] = image_data.get("url", "")
        story_data["image_page"] = image_data.get("page", "")
        story_data["image_credit"] = image_data.get("credit", "")
        
        email_sent = send_story_email(story_data)
        if not email_sent:
            log_message("Error: Failed to send email, aborting")
            return
        
        save_state(story_data, image_data)
        
        log_message(f"Success: Story '{story_data.get('slug')}' selected and emailed")
        log_message("Waiting for user response...")
        
    except Exception as e:
        log_message(f"Unexpected error in main: {e}")
        import traceback
        log_message(traceback.format_exc())
    
    log_message("RWS Daily Story Automation Completed")
    log_message("=" * 60)


if __name__ == "__main__":
    main()
