# Red White & Skewed - Voting & Sharing Enhancement

## Overview

This package adds three new features to Red White & Skewed:

1. **"I Support This View" Voting** - Users can vote for conservative or liberal perspective
2. **Social Sharing** - Share buttons with "What side are you on?" call-to-action
3. **Automated Upload** - SFTP script to push stories directly to one.com

---

## Files Included

```
rws-voting/
├── vote_api.php       # PHP backend for voting (SQLite database)
├── app.js             # Updated story renderer with voting + sharing
├── voting-styles.css  # Styles for voting UI and share buttons
├── rws_upload.py      # SFTP upload automation script
└── README.md          # This file
```

---

## Setup Instructions

### Step 1: Enable SFTP on One.com

1. Log into **One.com Control Panel** for redwhiteandskewed.com
2. Go to **Advanced Settings → SSH & SFTP**
3. Toggle **"Allow SSH & SFTP access"** to **ON**
4. Click **"Send"** to get a password reset email
5. Set your SFTP password
6. Note your connection details:
   - Host: `ssh.redwhiteandskewed.com` (or as shown)
   - Username: `redwhiteandskewed.com`
   - Port: `22`

### Step 2: Install Python Dependencies

```bash
pip3 install paramiko
```

### Step 3: Configure Upload Script

Set environment variables (recommended) or edit `rws_upload.py`:

```bash
export RWS_SFTP_HOST="ssh.redwhiteandskewed.com"
export RWS_SFTP_USERNAME="redwhiteandskewed.com"
export RWS_SFTP_PASSWORD="your_sftp_password"
```

### Step 4: Test Connection

```bash
python3 rws_upload.py --test
```

### Step 5: Upload Files to Site

**First-time setup (upload everything):**

1. Create this folder structure locally:
   ```
   rws-site/
   ├── index.html
   ├── app.js              # (from this package)
   ├── voting-styles.css   # (from this package - merge into your CSS)
   ├── api/
   │   └── vote.php        # (from this package)
   └── stories/
       └── latest.json
   ```

2. Upload:
   ```bash
   python3 rws_upload.py --full ./rws-site
   ```

**Or upload components individually:**

```bash
# Upload API only
python3 rws_upload.py --api

# Upload a new story
python3 rws_upload.py --story ./stories/2026-01-15-story-slug.json
```

---

## Voting System Details

### How It Works

- **One vote per user per story** (conservative OR liberal, not both)
- **Vote changes allowed** - Users can switch their vote on return visits
- **Duplicate detection** via IP hash + browser fingerprint
- **Rate limiting** - 30 requests/hour, 100/day per IP
- **Archive/lock** - Votes can be locked when stories are archived

### Database

The PHP script creates a SQLite database at `/api/votes.db` with:
- `votes` table - Stores all votes
- `archived_stories` table - Tracks which stories have voting locked
- `rate_limits` table - Prevents abuse

### API Endpoints

**GET /api/vote.php?story_id=xxx**
- Returns vote status and results
- Response: `{ success, user_vote, results, archived }`

**POST /api/vote.php**
- Cast or change vote
- Body: `{ story_id, vote: "conservative"|"liberal", fingerprint }`
- Response: `{ success, user_vote, results, vote_changed }`

### Archiving Stories (Locking Votes)

To archive a story and lock voting:

```bash
curl -X POST https://redwhiteandskewed.com/api/vote.php \
  -H "Content-Type: application/json" \
  -d '{"story_id": "2026-01-15-story-slug", "action": "archive", "admin_key": "rws_admin_2026_CHANGE_THIS"}'
```

**Important:** Change the `admin_key` in `vote_api.php` to something secure!

---

## Social Sharing

Share buttons included:
- **Twitter/X** - Opens tweet composer
- **Facebook** - Opens share dialog
- **LinkedIn** - Opens share dialog
- **Email** - Opens email client
- **Copy Link** - Copies URL to clipboard

Default share text: *"I just read '[Story Title]' on Red White & Skewed — what side are you on?"*

---

## Integration with Existing Site

### Add to your HTML `<head>`:

```html
<link rel="stylesheet" href="voting-styles.css">
```

Or merge the CSS into your existing stylesheet.

### Add before `</body>`:

```html
<script src="app.js"></script>
```

### Required HTML structure:

```html
<div id="story-container"></div>
```

The app.js will automatically load and render stories into this container.

---

## Workflow: Creating & Publishing Stories

### 1. Create Story with Claude

In Claude, request a story:
> "Create today's Red White & Skewed story about [TOPIC]"

Claude generates a JSON file in the standard format.

### 2. Save the JSON

Save as: `YYYY-MM-DD-slug-title.json`
Example: `2026-01-15-trump-tariff-announcement.json`

### 3. Upload to Site

```bash
python3 rws_upload.py --story ./stories/2026-01-15-trump-tariff-announcement.json
```

This uploads the story AND updates `latest.json` automatically.

### 4. (Optional) Archive Old Stories

After a few days, archive to lock voting:

```bash
curl -X POST https://redwhiteandskewed.com/api/vote.php \
  -d '{"story_id": "2026-01-10-old-story", "action": "archive", "admin_key": "YOUR_KEY"}'
```

---

## Troubleshooting

### SFTP Connection Failed
- Verify SFTP is enabled in One.com Control Panel
- Check password is correct
- Ensure port 22 is not blocked by your network

### Voting Not Working
- Check browser console for errors
- Verify `/api/vote.php` is accessible
- Ensure `/api/` directory has write permissions for SQLite

### Votes Not Persisting
- Check that `votes.db` was created in `/api/`
- Verify PHP has permission to write to the directory

---

## Security Notes

1. **Change the admin_key** in `vote_api.php` immediately
2. **Never commit passwords** to git - use environment variables
3. **Consider adding .htaccess** to protect `/api/votes.db` from direct access:
   ```apache
   <Files "votes.db">
       Order Allow,Deny
       Deny from all
   </Files>
   ```

---

## Questions?

This system was built for Jim's Red White & Skewed project. Reach out via Claude if you need modifications!
