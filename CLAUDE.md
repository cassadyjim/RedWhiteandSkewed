# Red White & Skewed — Automation Project

## What This Is
Daily auto-publishing system for redwhiteandskewed.com. Each night it selects 10 story options using Claude AI with web search, emails them to Jim as a numbered list, waits for a reply (1–10), then generates and publishes the full story.

## Key Files

| File | Purpose |
|------|---------|
| `rws_daily_auto.py` | Nightly job: picks 10 stories, sends selection email, saves state |
| `rws_reply_monitor.py` | Runs every 30 min: checks IMAP for reply, publishes chosen story |
| `rws_story_prompt.md` | Active story-writing prompt (v10 with Quote Ledger) |
| `rws-story-prompt_v10.md` | Same as above, versioned backup |
| `state/pending_story.json` | Live state between selector and monitor runs |
| `story_history.json` | Log of published stories (used to avoid repeats) |
| `.github/workflows/daily_story_selector.yml` | Cron: runs at 2:00 AM UTC (10 PM EDT) |
| `.github/workflows/reply_monitor.yml` | Cron: runs every 30 minutes |
| `rws_to_wix.py` | Publishes story to Wix CMS via API |
| `rws_find_image.py` | Searches Pexels for story image |
| `rws_upload.py` / `rws_upload.sh` | SFTP upload to web host |

## Workflow

```
10 PM EDT: daily_story_selector.yml
  └─ rws_daily_auto.py
       ├─ select_story() → Claude picks 10 stories (JSON array, max_tokens=6000)
       ├─ send_story_email(stories) → numbered HTML email to jim@redwhiteandskewed.com
       └─ save_state(stories) → state/pending_story.json with email_sent_at + stories list

Every 30 min: reply_monitor.yml
  └─ rws_reply_monitor.py
       ├─ load state/pending_story.json
       ├─ check 20h timeout (email_sent_at → now)
       ├─ check IMAP for unread reply matching subject "rws" + ("story"/"choice"/"pick")
       ├─ validate reply timestamp > email_sent_at (UTC-normalized)
       ├─ extract option 1–10 with regex \b(10|[1-9])\b
       ├─ map: selected_story = stories[option - 1]
       └─ handle_option_1() → generate full story → publish to Wix → SFTP upload
```

## State File Format

```json
{
  "date": "2026-08-11",
  "email_sent_at": "2026-08-12T02:00:37",
  "stories": [
    {"title": "...", "angle": "...", "why_now": "...", "search_queries": [...]},
    ...
  ]
}
```

## Critical Bugs Fixed (Do Not Reintroduce)

### 1. GITHUB_TOKEN vs GH_PAT
Both workflows use `token: ${{ secrets.GITHUB_TOKEN }}` (built-in, auto-generated, never expires). Never use `secrets.GH_PAT` — it's a personal token that expires and will cause 4-second workflow failures on checkout.

### 2. git commit order matters
Always: `git add` → `git commit` → `git checkout -- .` → `git pull --rebase` → `git push`.
Never use `git stash` between `git add` and `git commit` — stash un-stages files, causing the commit to be skipped and state never saved.

### 3. Timezone comparison in IMAP check
`email_sent_at` is stored as naive UTC. IMAP `Date` headers include timezone offsets (e.g., `-0400` EDT). Must convert properly:
```python
reply_dt = parsedate_to_datetime(date_header)
if reply_dt.tzinfo is not None:
    reply_utc_naive = reply_dt.astimezone(datetime.timezone.utc).replace(tzinfo=None)
```
Stripping `.tzinfo` without converting first gives local time — a 12:18 EDT reply becomes "12:18" which incorrectly appears before a "16:17 UTC" sent time.

### 4. IMAP subject filter
Selector email subject: `"🗞️ RWS Story Choices — {date} — Reply 1–10 to Publish"`
Reply monitor filter must match with: `any(k in subj_lower for k in ["story", "pick", "choice"])`
Do NOT use a single fixed substring like `"rws daily story pick"`.

### 5. Timeout window
20 hours (not 11). Email sent at 10 PM EDT; Jim typically replies next day at noon = 14 hours.

## GitHub Secrets Required

| Secret | Used For |
|--------|---------|
| `ANTHROPIC_API_KEY` | Story generation (Claude) |
| `PEXELS_API_KEY` | Story images |
| `SMTP_PASSWORD` | Sending emails via one.com |
| `IMAP_PASSWORD` | Reading replies via one.com |
| `RWS_SFTP_HOST` / `RWS_SFTP_USERNAME` / `RWS_SFTP_PASSWORD` | SFTP upload |
| `WIX_API_KEY` / `WIX_SITE_ID` / `WIX_COLLECTION_ID` | Wix CMS publish |

## Email Config

- SMTP: `send.one.com:465` (SSL)
- IMAP: `imap.one.com:993`
- From/reply inbox: `info@redwhiteandskewed.com`
- Failure notifications go to: `jim@redwhiteandskewed.com`

## Story Prompt (v10)

The prompt uses a **3-phase approach with Quote Ledger**:
1. **Research** — web_search_20250305 tool, gather facts
2. **Quote Ledger** — document all direct quotes with URLs before writing
3. **Write** — produce full story from ledger (prevents fabricated quotes)

Story format: satirical political commentary, 500–700 words, HTML output for Wix.

## Wix Publishing

`rws_to_wix.py` uses Wix Content Manager API v2. Stories are published to a Wix collection, then `latest.json` is updated for the site's homepage widget.

## Common Debugging

**Workflow fails in ~4 seconds**: Expired GH_PAT — make sure both workflows use `GITHUB_TOKEN`.

**State not saving**: Check git commit order in workflow YAML. The `git stash` pattern breaks staging.

**Reply not detected**: Check IMAP subject filter and verify `email_sent_at` in state file is recent. Stale state (from the git stash bug) can leave a March timestamp that immediately times out.

**Reply detected but skipped**: Timezone bug — verify the UTC conversion logic in `check_imap_for_reply()`.

**GitHub Actions budget exhausted**: Add budget to the "Actions" line item in GitHub billing settings (not "All Premium Request SKUs").
