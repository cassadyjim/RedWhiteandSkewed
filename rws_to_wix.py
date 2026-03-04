#!/usr/bin/env python3
"""
Red White & Skewed — Wix CMS Publisher
Converts an RWS story JSON file and pushes it directly to the Wix CMS via REST API.

Usage:
    python3 rws_to_wix.py story.json              # Insert new story
    python3 rws_to_wix.py story.json --update     # Update existing story by slug
    python3 rws_to_wix.py --test                  # Test API connection

Setup:
    Add to your .env file:
        WIX_API_KEY=your_api_key_here
        WIX_SITE_ID=your_site_id_here
        WIX_COLLECTION_ID=redwhiteandskeweddifferance   (or your collection name)

    Get your API key: Wix Dashboard → Settings → API Keys
    Get your Site ID: from your Wix dashboard URL or Settings → General Info
"""

import os
import sys
import json
import uuid
import re
import argparse
from datetime import datetime, timezone
from pathlib import Path

try:
    import urllib.request
    import urllib.error
except ImportError:
    pass


# ============================================
# LOAD CREDENTIALS FROM .env
# ============================================

def load_env():
    env_path = Path(__file__).parent / '.env'
    if not env_path.exists():
        # In GitHub Actions, credentials come from environment variables — this is fine
        return
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, _, val = line.partition('=')
                os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))

load_env()

WIX_API_KEY     = os.environ.get('WIX_API_KEY', '').strip()
WIX_SITE_ID     = os.environ.get('WIX_SITE_ID', '').strip()
WIX_COLLECTION  = os.environ.get('WIX_COLLECTION_ID', 'redwhiteandskeweddifferance').strip()
WIX_API_BASE    = 'https://www.wixapis.com/wix-data/v2/items'


# ============================================
# FIELD MAPPING HELPERS
# ============================================

def slugify(text):
    """Convert title to URL slug: 'Hello World' → 'Hello-World'"""
    text = re.sub(r"[''']", '', text)          # Remove smart quotes
    text = re.sub(r'[^a-zA-Z0-9\s-]', '', text)  # Strip special chars
    text = re.sub(r'\s+', '-', text.strip())       # Spaces → hyphens
    return text


def strip_html(text):
    """Strip all HTML tags to get plain text — used for summary/conclusion fields."""
    return re.sub(r'<[^>]+>', '', text).strip()


# Block-level tags that should NOT be wrapped in an extra <p>
BLOCK_TAGS = re.compile(r'^<(p|div|ul|ol|li|h[1-6]|blockquote|table|figure)[\s>]', re.I)

# Match <a> tags that don't already have a style attribute
UNSTYLED_LINK = re.compile(r'<a\s((?!style=)[^>])*>', re.I)

def style_links(html):
    """Add red underline style to every <a> tag that doesn't already have one."""
    def add_style(m):
        tag = m.group(0)
        # Already has style — leave it
        if 'style=' in tag:
            return tag
        # Ensure rel and target are present, then add style
        if 'rel=' not in tag:
            tag = tag[:-1] + ' rel="noopener noreferrer">'
        if 'target=' not in tag:
            tag = tag[:-1] + ' target="_blank">'
        tag = tag[:-1] + ' style="color: red; text-decoration: underline;">'
        return tag
    return re.sub(r'<a\s[^>]*>', add_style, html, flags=re.I)


def paragraphs_to_html(paragraphs):
    """Join RWS paragraph list into HTML.
    - Block-level tags (<p>, <div>, etc.) are kept as-is.
    - Everything else (plain text, <strong>, <a>, etc.) is wrapped in <p>.
    - Section header paragraphs (class="text-xl...") are skipped.
    - All <a> tags get red underline styling.
    - Paragraphs are separated by a blank line (\\n\\n) for visual spacing in Wix.
    """
    parts = []
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        # Skip Tailwind-styled section headers (they're structural, not content)
        if 'class="text-xl' in p or 'text-purple-900' in p:
            continue
        if BLOCK_TAGS.match(p):
            # Inject margin-bottom into <p> tags; leave other block tags as-is
            p = p.replace('<p>', '<p style="margin-bottom: 1.2em;">', 1)
            parts.append(style_links(p))
        else:
            parts.append(style_links(f'<p style="margin-bottom: 1.2em;">{p}</p>'))
    return '\n'.join(parts)


def sources_to_html(sources):
    """Convert RWS sources list to HTML with red underline styling to match Wix format."""
    if not sources:
        return ''
    items = []
    for src in sources:
        if isinstance(src, dict):
            text = src.get('text', '')
            url  = src.get('url', '')
            if url:
                items.append(
                    f'<a href="{url}" rel="noopener noreferrer" target="_blank" '
                    f'style="color: red; text-decoration: underline;">{text}</a>'
                )
            else:
                items.append(text)
        else:
            items.append(str(src))
    return '<p>' + '</p>\n\n<p>'.join(items) + '</p>'


def parse_date_to_iso(date_str):
    """Convert 'February 5, 2026' → '2026-02-05T12:00:00Z'"""
    try:
        dt = datetime.strptime(date_str, '%B %d, %Y')
        return dt.strftime('%Y-%m-%dT12:00:00Z')
    except Exception:
        return datetime.now(timezone.utc).strftime('%Y-%m-%dT12:00:00Z')


def split_factcheck_sections(paragraphs):
    """
    Split the flat factcheck paragraphs list into the four Wix CMS sections:
      - summary        (first paragraph)
      - undisputed     (paragraphs between UNDISPUTED FACTS and CONSERVATIVE SPIN headers)
      - red_spin       (paragraphs between CONSERVATIVE SPIN and LIBERAL SPIN headers)
      - blue_spin      (paragraphs between LIBERAL SPIN and BIGGER PICTURE headers)
      - big_picture    (paragraphs from BIGGER PICTURE header onward)

    Headers are detected by their content (they contain section title keywords).
    """
    HEADERS = {
        'undisputed':  re.compile(r'UNDISPUTED FACTS', re.I),
        'red_spin':    re.compile(r'CONSERVATIVE SPIN', re.I),
        'blue_spin':   re.compile(r'LIBERAL SPIN', re.I),
        'big_picture': re.compile(r'BIGGER PICTURE|BIG PICTURE', re.I),
    }

    summary = paragraphs[0] if paragraphs else ''
    sections = {k: [] for k in HEADERS}
    current = None

    for p in paragraphs[1:]:
        matched = False
        for key, pattern in HEADERS.items():
            if pattern.search(p):
                current = key
                matched = True
                break
        if not matched and current:
            sections[current].append(p)

    return {
        'summary':    summary,
        'undisputed': paragraphs_to_html(sections['undisputed']),
        'red_spin':   paragraphs_to_html(sections['red_spin']),
        'blue_spin':  paragraphs_to_html(sections['blue_spin']),
        'big_picture':paragraphs_to_html(sections['big_picture']),
    }


# ============================================
# MAP RWS JSON → WIX CMS DATA ITEM
# ============================================
# NOTE: The keys below (e.g. "article_Title") must match the Field IDs
# in your Wix CMS collection exactly. If a field isn't mapping correctly,
# open Wix Dashboard → CMS → your collection → field settings and copy
# the Field ID shown there.
# ============================================

def rws_to_wix_item(story, item_id=None):
    """Return a Wix dataItem.data dict from an RWS story JSON object."""

    slug        = slugify(story.get('title', ''))
    title       = story.get('title', '')
    subtitle    = story.get('subtitle', '')
    date_str    = story.get('date', '')
    iso_date    = parse_date_to_iso(date_str)
    now_iso     = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    item_id     = item_id or str(uuid.uuid4())

    con  = story.get('conservative', {})
    lib  = story.get('liberal', {})
    fact = story.get('factcheck', {})
    img  = story.get('image', {})

    fact_sections = split_factcheck_sections(fact.get('paragraphs', []))

    # Conservative section
    # summary = first paragraph (plain text), conclusion = last paragraph (plain text)
    # body = MIDDLE paragraphs only — Wix template renders: summary → body → conclusion
    con_paras      = con.get('paragraphs', [])
    con_summary    = strip_html(con_paras[0]) if con_paras else ''
    con_conclusion = strip_html(con_paras[-1]) if len(con_paras) > 1 else ''
    con_body       = paragraphs_to_html(con_paras[1:-1] if len(con_paras) > 2 else [])

    # Liberal section
    lib_paras      = lib.get('paragraphs', [])
    lib_summary    = strip_html(lib_paras[0]) if lib_paras else ''
    lib_conclusion = strip_html(lib_paras[-1]) if len(lib_paras) > 1 else ''
    lib_body       = paragraphs_to_html(lib_paras[1:-1] if len(lib_paras) > 2 else [])

    # Fact check full body (all paragraphs)
    fact_body      = paragraphs_to_html(fact.get('paragraphs', []))

    return {
        # ── Wix system fields ─────────────────────────────────────────────
        '_id':            item_id,
        '_publishStatus': 'PUBLISHED',

        # ── Slug / URL ────────────────────────────────────────────────────
        'title':          slug,

        # ── Article titles ────────────────────────────────────────────────
        'article_title':      title,
        'shortDescription':   subtitle,       # RICH_TEXT — Article_Sub_Title
        'article_sub_title':  subtitle,       # TEXT — Article_Sub_Title
        'article_title_new':  title,

        # ── Conservative (Red) section ────────────────────────────────────
        'article_red_title':        con.get('headline', ''),
        'article_red_title_byline': con.get('byline', ''),
        'article_red_summary':      con_summary,
        'articleRed':               con_body,           # RICH_TEXT
        'article_red_conclusion':   con_conclusion,
        'article_red_sources':      sources_to_html(con.get('sources', [])),  # RICH_TEXT

        # ── Liberal (Blue) section ────────────────────────────────────────
        'article_blue_title':        lib.get('headline', ''),
        'article_blue_title_byline': lib.get('byline', ''),
        'article_blue_summary':      lib_summary,
        'articleBlue':               lib_body,           # RICH_TEXT
        'article_blue_conclusion':   lib_conclusion,
        'article_blue_sources':      sources_to_html(lib.get('sources', [])),  # RICH_TEXT

        # ── Fact Check (Truth) section ────────────────────────────────────
        'article_truth_summary':      strip_html(fact_sections['summary']),  # Plain text
        'articleTruth':               fact_body,                               # RICH_TEXT
        'truth_undisputed_facts':     fact_sections['undisputed'],             # RICH_TEXT
        'truth_red_spin_vs_reality':  fact_sections['red_spin'],               # RICH_TEXT
        'truth_blue_spin_vs_reality': fact_sections['blue_spin'],              # RICH_TEXT
        'truth_big_picture':          fact_sections['big_picture'],            # RICH_TEXT
        'truth_sources':              sources_to_html(fact.get('sources', [])),# RICH_TEXT

        # ── Image ─────────────────────────────────────────────────────────
        'image':         img.get('url', ''),   # IMAGE field
        'imageAltText':  img.get('alt', ''),   # TEXT
        'header_image':  img.get('url', ''),   # TEXT — external URL backup

        # ── Item path ─────────────────────────────────────────────────────
        'redwhiteandskeweddifferanceItem': f'/{WIX_COLLECTION}/{slug}',  # URL

        # ── Publish date ──────────────────────────────────────────────────
        'publishDate':   iso_date,             # DATETIME
    }


# ============================================
# WIX REST API CALLS
# ============================================

def wix_headers():
    return {
        'Authorization': WIX_API_KEY,
        'wix-site-id':   WIX_SITE_ID,
        'Content-Type':  'application/json',
    }


def wix_request(method, url, body=None):
    data = json.dumps(body).encode() if body else None
    req  = urllib.request.Request(url, data=data, headers=wix_headers(), method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        err_body = e.read().decode()
        print(f"❌ HTTP {e.code}: {e.reason}")
        print(f"   {err_body[:500]}")
        return None
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return None


def fetch_schema():
    """Fetch and display all field IDs defined in the Wix CMS collection."""
    result = wix_request('GET',
        f'https://www.wixapis.com/wix-data/v2/collections/{WIX_COLLECTION}')
    if not result:
        return False
    collection = result.get('collection', result)
    fields = collection.get('fields', [])
    print(f"\n📋 Collection: {collection.get('id', WIX_COLLECTION)}")
    print(f"   Display name: {collection.get('displayName', '')}")
    print(f"\n{'Field ID':<40} {'Display Name':<35} {'Type'}")
    print('-' * 90)
    for f in fields:
        fid   = f.get('key') or f.get('id', '')
        fname = f.get('displayName') or f.get('name', '')
        ftype = f.get('type', '')
        if isinstance(ftype, dict):
            ftype = ftype.get('name', str(ftype))
        print(f"   {fid:<38} {fname:<35} {ftype}")
    return True


def find_item_by_slug(slug):
    """Query Wix CMS for an existing item by its slug (title field)."""
    body = {
        'dataCollectionId': WIX_COLLECTION,
        'query': {
            'filter': {'title': {'$eq': slug}},
            'paging': {'limit': 1}
        }
    }
    result = wix_request('POST', 'https://www.wixapis.com/wix-data/v2/items/query', body)
    if result and result.get('dataItems'):
        return result['dataItems'][0]
    return None


def insert_item(item_data):
    item_id = item_data.get('_id', str(uuid.uuid4()))
    body = {
        'dataCollectionId': WIX_COLLECTION,
        'dataItem': {
            'id':   item_id,
            'data': item_data
        }
    }
    return wix_request('POST', WIX_API_BASE, body)


def update_item(item_id, item_data):
    item_data['_id'] = item_id  # Keep _id in data in sync
    body = {
        'dataCollectionId': WIX_COLLECTION,
        'dataItem': {
            'id':   item_id,
            'data': item_data
        }
    }
    return wix_request('PUT', f'{WIX_API_BASE}/{item_id}', body)


def test_connection():
    """List the first few items in the collection to verify connectivity."""
    body = {
        'dataCollectionId': WIX_COLLECTION,
        'query': {'paging': {'limit': 3}}
    }
    result = wix_request('POST', 'https://www.wixapis.com/wix-data/v2/items/query', body)
    if result:
        items = result.get('dataItems', [])
        print(f"✅ Connected! Found {len(items)} item(s) in '{WIX_COLLECTION}':")
        for item in items:
            print(f"   • {item.get('data', {}).get('title', '(no title)')}")
        return True
    return False


# ============================================
# MAIN
# ============================================

def main():
    parser = argparse.ArgumentParser(
        description='Red White & Skewed — Push story to Wix CMS',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 rws_to_wix.py story.json            # Insert new story
  python3 rws_to_wix.py story.json --update   # Update if exists, insert if not
  python3 rws_to_wix.py --test                # Test connection
        """
    )
    parser.add_argument('story', nargs='?', help='Path to RWS story JSON file')
    parser.add_argument('--update', action='store_true',
                        help='Update an existing item (matched by slug) instead of always inserting')
    parser.add_argument('--test',   action='store_true', help='Test Wix API connection')
    parser.add_argument('--schema', action='store_true', help='Show all field IDs in the Wix collection')
    args = parser.parse_args()

    print()
    print('=' * 50)
    print('  Red White & Skewed — Wix CMS Publisher')
    print('=' * 50)
    print(f'  Collection: {WIX_COLLECTION}')
    print(f'  Site ID:    {WIX_SITE_ID[:8]}...' if WIX_SITE_ID else '  Site ID:    (NOT SET)')
    print(f'  API Key:    {WIX_API_KEY[:8]}...' if WIX_API_KEY else '  API Key:    (NOT SET)')
    print('=' * 50)
    print()

    if not WIX_API_KEY or not WIX_SITE_ID:
        print('❌ WIX_API_KEY and WIX_SITE_ID must be set in your .env file.')
        print('   Get your API key: Wix Dashboard → Settings → API Keys')
        print('   Get your Site ID: your Wix dashboard URL or Settings → General Info')
        sys.exit(1)

    if args.test:
        test_connection()
        return

    if args.schema:
        fetch_schema()
        return

    if not args.story:
        parser.print_help()
        sys.exit(1)

    story_path = Path(args.story)
    if not story_path.exists():
        # Try relative to script dir
        story_path = Path(__file__).parent / args.story
    if not story_path.exists():
        print(f'❌ Story file not found: {args.story}')
        sys.exit(1)

    with open(story_path) as f:
        story = json.load(f)

    slug = slugify(story.get('title', ''))
    print(f'📰 Story: {story.get("title", "")}')
    print(f'   Slug:  {slug}')
    print()

    item_data = rws_to_wix_item(story)

    if args.update:
        print(f'🔍 Checking for existing item with slug "{slug}"...')
        existing = find_item_by_slug(slug)
        if existing:
            existing_id = existing.get('id') or existing.get('_id')
            print(f'   Found existing item: {existing_id}')
            print(f'⬆️  Updating...')
            result = update_item(existing_id, item_data)
        else:
            print(f'   No existing item found — inserting new.')
            result = insert_item(item_data)
    else:
        print(f'➕ Inserting new item...')
        result = insert_item(item_data)

    if result:
        item = result.get('dataItem', {})
        item_id = item.get('id') or item.get('_id', '?')
        print()
        print('=' * 50)
        print('  ✅ PUBLISHED TO WIX CMS!')
        print('=' * 50)
        print(f'  Item ID:    {item_id}')
        print(f'  Slug:       {slug}')
        print(f'  Collection: {WIX_COLLECTION}')
        print()
    else:
        print()
        print('❌ Publish failed. See error above.')
        sys.exit(1)


if __name__ == '__main__':
    main()
