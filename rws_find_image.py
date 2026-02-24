#!/usr/bin/env python3
"""
Red White & Skewed - Image Finder
Searches royalty-free sources for a story image.

Usage:
    python3 rws_find_image.py "Trump elections voting nationalize"
    python3 rws_find_image.py "EPA climate regulations"

Sources searched:
    1. Wikimedia Commons (public domain / CC licensed)
    2. White House Flickr (all public domain)
"""

import sys
import json
import urllib.request
import urllib.parse

# ============================================================
# CONFIG
# ============================================================

WIKIMEDIA_API = "https://commons.wikimedia.org/w/api.php"
FLICKR_API    = "https://api.flickr.com/services/rest/"

# White House Flickr account ID (public domain - all photos)
WHITEHOUSE_FLICKR_USER = "35591378@N03"

# No Flickr API key needed for White House - we use public RSS/URL tricks
# But for full search we use the public API with no-auth endpoints
FLICKR_PUBLIC_FEED = "https://www.flickr.com/services/feeds/photos_public.gne"

# ============================================================
# WIKIMEDIA COMMONS SEARCH
# ============================================================

def search_wikimedia(query, limit=5):
    """Search Wikimedia Commons for freely licensed images."""
    params = {
        "action": "query",
        "generator": "search",
        "gsrnamespace": "6",      # File namespace
        "gsrsearch": f"filetype:bitmap {query}",
        "gsrlimit": str(limit),
        "prop": "imageinfo",
        "iiprop": "url|extmetadata",
        "iiurlwidth": "1200",
        "format": "json",
    }

    url = WIKIMEDIA_API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "RWS-ImageFinder/1.0"})

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        print(f"  ⚠️  Wikimedia search failed: {e}")
        return []

    pages = data.get("query", {}).get("pages", {})
    results = []

    for page in pages.values():
        info_list = page.get("imageinfo", [])
        if not info_list:
            continue
        info = info_list[0]
        meta = info.get("extmetadata", {})

        title       = page.get("title", "").replace("File:", "")
        image_url   = info.get("thumburl") or info.get("url", "")
        page_url    = info.get("descriptionurl", "")
        license_url = meta.get("LicenseUrl", {}).get("value", "")
        license_name= meta.get("LicenseShortName", {}).get("value", "Unknown")
        artist      = meta.get("Artist", {}).get("value", "Unknown")
        description = meta.get("ImageDescription", {}).get("value", "")

        # Strip HTML tags from artist/description
        import re
        artist      = re.sub(r"<[^>]+>", "", artist).strip()
        description = re.sub(r"<[^>]+>", "", description).strip()[:120]

        results.append({
            "source":      "Wikimedia Commons",
            "title":       title,
            "image_url":   image_url,
            "page_url":    page_url,
            "license":     license_name,
            "license_url": license_url,
            "credit":      artist if artist else "Wikimedia Commons",
            "description": description,
        })

    return results


# ============================================================
# WHITE HOUSE FLICKR SEARCH (Public Domain)
# ============================================================

def search_whitehouse_flickr(query, limit=5):
    """
    Search the White House public Flickr feed.
    All White House photos are public domain (U.S. government works).
    Uses Flickr's public feed (no API key required).
    """
    params = {
        "format": "json",
        "nojsoncallback": "1",
        "id":   WHITEHOUSE_FLICKR_USER,
        "tags": query.replace(" ", ","),
    }

    url = FLICKR_PUBLIC_FEED + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "RWS-ImageFinder/1.0"})

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        print(f"  ⚠️  White House Flickr search failed: {e}")
        return []

    items = data.get("items", [])[:limit]
    results = []

    for item in items:
        media = item.get("media", {})
        image_url = media.get("m", "").replace("_m.jpg", "_b.jpg")  # Get larger size
        page_url  = item.get("link", "")
        title     = item.get("title", "")
        author    = item.get("author", "").split('"')[-2] if '"' in item.get("author","") else "White House"

        results.append({
            "source":      "White House Flickr",
            "title":       title,
            "image_url":   image_url,
            "page_url":    page_url,
            "license":     "Public Domain (U.S. Government Work)",
            "license_url": "https://www.usa.gov/government-works",
            "credit":      f"Official White House Photo",
            "description": title,
        })

    return results


# ============================================================
# PRINT RESULTS
# ============================================================

def print_results(results, source_label):
    if not results:
        print(f"  No results found from {source_label}.")
        return

    for i, r in enumerate(results, 1):
        print(f"\n  [{i}] {r['title'][:70]}")
        print(f"      License : {r['license']}")
        print(f"      Credit  : {r['credit']}")
        print(f"      Image   : {r['image_url']}")
        print(f"      Page    : {r['page_url']}")
        if r.get("description"):
            print(f"      Desc    : {r['description'][:100]}")


def print_json_snippet(result):
    """Print the JSON snippet to paste into your story file."""
    snippet = {
        "image": {
            "url":    result["image_url"],
            "credit": result["credit"],
            "alt":    result.get("description") or result["title"],
            "source": result["source"],
            "page":   result["page_url"],
            "license":result["license"],
        }
    }
    print("\n" + "="*60)
    print("  PASTE THIS INTO YOUR STORY JSON:")
    print("="*60)
    print(json.dumps(snippet, indent=2))


# ============================================================
# MAIN
# ============================================================

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 rws_find_image.py \"your search terms\"")
        print("Example: python3 rws_find_image.py \"Trump voting elections\"")
        sys.exit(1)

    query = " ".join(sys.argv[1:])

    print()
    print("=" * 60)
    print("  Red White & Skewed - Image Finder")
    print("=" * 60)
    print(f"  Searching for: {query}")
    print()

    # --- White House Flickr ---
    print("📸 WHITE HOUSE FLICKR (Public Domain):")
    print("-" * 50)
    wh_results = search_whitehouse_flickr(query, limit=5)
    print_results(wh_results, "White House Flickr")

    print()

    # --- Wikimedia Commons ---
    print("🌐 WIKIMEDIA COMMONS (Free License):")
    print("-" * 50)
    wm_results = search_wikimedia(query, limit=5)
    print_results(wm_results, "Wikimedia Commons")

    # --- Prompt to pick one ---
    all_results = wh_results + wm_results
    if not all_results:
        print("\n❌ No results found. Try different keywords.")
        sys.exit(1)

    print()
    print("=" * 60)
    print("  ADDITIONAL SOURCES TO CHECK MANUALLY:")
    print("=" * 60)
    wh_search = urllib.parse.quote(query)
    print(f"  White House Flickr : https://www.flickr.com/photos/whitehouse/search/?q={wh_search}")
    wm_search  = urllib.parse.quote(query)
    print(f"  Wikimedia Commons  : https://commons.wikimedia.org/w/index.php?search={wm_search}&ns6=1")
    print(f"  Congress Photos    : https://www.flickr.com/photos/uscapitol/search/?q={wh_search}")
    print()

    # --- Pick one to generate JSON ---
    try:
        choice = input("Enter a number to generate the JSON snippet (or press Enter to skip): ").strip()
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(all_results):
                print_json_snippet(all_results[idx])
            else:
                print("Invalid selection.")
    except (KeyboardInterrupt, EOFError):
        pass

    print()


if __name__ == "__main__":
    main()
