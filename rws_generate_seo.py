#!/usr/bin/env python3
"""
rws_generate_seo.py

Generates sitemap.xml and feed.xml (RSS) from all story JSON files.
Run after publishing a new story, or run standalone to regenerate everything.

Usage:
    python3 rws_generate_seo.py
"""

import json
import os
import re
import glob
import pathlib
import datetime
from xml.sax.saxutils import escape

SCRIPT_DIR = pathlib.Path(__file__).parent
BASE_URL = "https://www.redwhiteandskewed.com"
STORIES_DIR = SCRIPT_DIR  # Story JSONs are in the root


def get_story_files():
    """Return list of (slug, filepath) for all story JSON files, newest first."""
    files = sorted(SCRIPT_DIR.glob("2[0-9][0-9][0-9]-*.json"), reverse=True)
    results = []
    for f in files:
        slug = f.stem  # e.g. 2026-08-12-trump-supreme-court
        results.append((slug, f))
    return results


def load_story(filepath):
    """Load and return a story JSON dict, or None on error."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"  Warning: could not read {filepath}: {e}")
        return None


def strip_html(text):
    """Remove HTML tags from a string."""
    return re.sub(r"<[^>]+>", "", text or "")


def story_description(story):
    """Build a plain-text description from conservative + liberal first paragraphs."""
    con_paras = story.get("conservative", {}).get("paragraphs", [])
    lib_paras = story.get("liberal", {}).get("paragraphs", [])
    con_text = strip_html(con_paras[0]) if con_paras else ""
    lib_text = strip_html(lib_paras[0]) if lib_paras else ""
    subtitle = strip_html(story.get("subtitle", ""))
    if subtitle:
        return subtitle[:200]
    if con_text:
        return con_text[:200]
    return ""


def parse_story_date(story, slug):
    """Return a datetime from the story JSON date field or slug."""
    date_str = story.get("date", "")
    # Try parsing "January 16, 2026" format
    for fmt in ("%B %d, %Y", "%B %d, %Y", "%Y-%m-%d"):
        try:
            return datetime.datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            pass
    # Fall back to slug date (YYYY-MM-DD-...)
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", slug)
    if m:
        return datetime.datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return datetime.datetime.now()


def generate_sitemap(story_files):
    """Generate sitemap.xml listing all static pages + story pages."""
    static_pages = [
        ("", "1.0", "daily"),
        ("archive.html", "0.8", "daily"),
        ("about.html", "0.6", "monthly"),
        ("faq.html", "0.6", "monthly"),
        ("how-we-fact-check.html", "0.6", "monthly"),
    ]

    lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')

    today = datetime.date.today().isoformat()

    # Static pages
    for page, priority, freq in static_pages:
        url = f"{BASE_URL}/{page}" if page else BASE_URL + "/"
        lines.append(f"""  <url>
    <loc>{url}</loc>
    <lastmod>{today}</lastmod>
    <changefreq>{freq}</changefreq>
    <priority>{priority}</priority>
  </url>""")

    # Story pages
    for slug, filepath in story_files:
        story = load_story(filepath)
        if not story:
            continue
        dt = parse_story_date(story, slug)
        lastmod = dt.strftime("%Y-%m-%d")
        url = f"{BASE_URL}/stories/{slug}.html"
        lines.append(f"""  <url>
    <loc>{url}</loc>
    <lastmod>{lastmod}</lastmod>
    <changefreq>never</changefreq>
    <priority>0.7</priority>
  </url>""")

    lines.append("</urlset>")
    output = "\n".join(lines)

    out_path = SCRIPT_DIR / "sitemap.xml"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(output)
    print(f"Generated sitemap.xml with {len(story_files)} stories + {len(static_pages)} static pages")
    return out_path


def generate_rss(story_files):
    """Generate feed.xml (RSS 2.0) from all stories."""
    now_rfc = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")

    items = []
    for slug, filepath in story_files[:50]:  # Cap at 50 most recent
        story = load_story(filepath)
        if not story:
            continue
        title = escape(story.get("title", "Untitled"))
        description = escape(story_description(story))
        dt = parse_story_date(story, slug)
        pub_date = dt.strftime("%a, %d %b %Y 12:00:00 +0000")
        link = f"{BASE_URL}/stories/{slug}.html"
        image = story.get("image", {})
        image_url = image.get("url", "")

        enclosure = ""
        if image_url:
            enclosure = f'<enclosure url="{escape(image_url)}" length="0" type="image/jpeg"/>'

        con_headline = escape(story.get("conservative", {}).get("headline", ""))
        lib_headline = escape(story.get("liberal", {}).get("headline", ""))
        full_desc = description
        if con_headline:
            full_desc += f" | Right: {con_headline}"
        if lib_headline:
            full_desc += f" | Left: {lib_headline}"

        items.append(f"""  <item>
    <title>{title}</title>
    <link>{link}</link>
    <guid isPermaLink="true">{link}</guid>
    <pubDate>{pub_date}</pubDate>
    <description>{full_desc}</description>
    {enclosure}
  </item>""")

    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Red, White, and Skewed</title>
    <link>{BASE_URL}/</link>
    <description>The same news story. Conservative framing. Liberal framing. Fact-checked. You decide.</description>
    <language>en-us</language>
    <lastBuildDate>{now_rfc}</lastBuildDate>
    <atom:link href="{BASE_URL}/feed.xml" rel="self" type="application/rss+xml"/>
    <image>
      <url>{BASE_URL}/rws-social-share.png</url>
      <title>Red, White, and Skewed</title>
      <link>{BASE_URL}/</link>
    </image>
{chr(10).join(items)}
  </channel>
</rss>"""

    out_path = SCRIPT_DIR / "feed.xml"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(rss)
    print(f"Generated feed.xml with {len(items)} items")
    return out_path


def generate_story_page(slug, story, out_dir):
    """Generate a static HTML page for a single story."""
    title = story.get("title", "Untitled")
    subtitle = story.get("subtitle", "")
    date_str = story.get("date", "")
    image = story.get("image", {})
    image_url = image.get("url", "")
    image_credit = image.get("credit", "")
    image_alt = image.get("alt", title)
    poll = story.get("poll", {})
    con = story.get("conservative", {})
    lib = story.get("liberal", {})
    factcheck = story.get("factcheck", {})

    page_url = f"https://www.redwhiteandskewed.com/stories/{slug}.html"
    description = strip_html(subtitle) or strip_html(title)

    # JSON-LD NewsArticle structured data
    jsonld = {
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "headline": title,
        "description": description[:200],
        "datePublished": slug[:10],  # YYYY-MM-DD from filename
        "dateModified": slug[:10],
        "url": page_url,
        "publisher": {
            "@type": "Organization",
            "name": "Red, White, and Skewed",
            "url": "https://www.redwhiteandskewed.com",
            "logo": {
                "@type": "ImageObject",
                "url": "https://www.redwhiteandskewed.com/rws-social-share.png"
            }
        },
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": page_url
        }
    }
    if image_url:
        jsonld["image"] = {"@type": "ImageObject", "url": image_url}

    def render_section(section, color_class, border_color):
        if not section:
            return ""
        headline = section.get("headline", "")
        byline = section.get("byline", "")
        paragraphs = section.get("paragraphs", [])
        sources = section.get("sources", [])

        paras_html = "\n".join(
            f'<p class="mb-4 leading-relaxed">{p}</p>' for p in paragraphs
        )
        sources_html = ""
        if sources:
            src_items = "\n".join(
                f'<li><a href="{s.get("url","")}" target="_blank" rel="noopener noreferrer" '
                f'class="underline hover:opacity-80">{s.get("text", s.get("url",""))}</a></li>'
                for s in sources if s.get("url")
            )
            sources_html = f'<div class="mt-6 pt-4 border-t border-gray-200"><p class="text-xs font-semibold uppercase tracking-wide text-gray-500 mb-2">Sources</p><ul class="text-xs space-y-1 text-gray-600">{src_items}</ul></div>'

        return f"""
        <div class="rounded-xl border-2 {border_color} p-6 mb-6">
          <p class="text-xs font-semibold uppercase tracking-widest text-gray-500 mb-2">{byline}</p>
          <h2 class="{color_class} text-xl font-bold mb-4">{headline}</h2>
          <div class="text-gray-800 text-base">{paras_html}</div>
          {sources_html}
        </div>"""

    con_html = render_section(con, "text-red-700", "border-red-200")
    lib_html = render_section(lib, "text-blue-700", "border-blue-200")

    factcheck_html = ""
    if factcheck:
        fc_headline = factcheck.get("headline", "")
        fc_paras = factcheck.get("paragraphs", [])
        fc_sources = factcheck.get("sources", [])
        fc_paras_html = "\n".join(f'<p class="mb-4 leading-relaxed">{p}</p>' for p in fc_paras)
        fc_src_html = ""
        if fc_sources:
            fc_src_items = "\n".join(
                f'<li><a href="{s.get("url","")}" target="_blank" rel="noopener noreferrer" '
                f'class="underline hover:opacity-80">{s.get("text", s.get("url",""))}</a></li>'
                for s in fc_sources if s.get("url")
            )
            fc_src_html = f'<ul class="text-xs space-y-1 text-gray-600 mt-2">{fc_src_items}</ul>'
        factcheck_html = f"""
        <div class="rounded-xl border-2 border-purple-200 p-6 mb-6">
          <p class="text-xs font-semibold uppercase tracking-widest text-purple-500 mb-2">Fact Check</p>
          <h2 class="text-purple-700 text-xl font-bold mb-4">{fc_headline}</h2>
          <div class="text-gray-800 text-base">{fc_paras_html}</div>
          {fc_src_html}
        </div>"""

    image_html = ""
    if image_url:
        image_html = f"""
        <div class="mb-6">
          <img src="{image_url}" alt="{image_alt}" class="w-full rounded-xl object-cover max-h-96">
          <p class="text-xs text-gray-500 mt-1 text-center">{image_credit}</p>
        </div>"""

    poll_html = ""
    if poll:
        pq = poll.get("question", "")
        opts = poll.get("options", [])
        if pq and len(opts) >= 2:
            # Handle both {label, description} dicts and plain strings
            opt0 = opts[0].get("label", opts[0]) if isinstance(opts[0], dict) else opts[0]
            opt1 = opts[1].get("label", opts[1]) if isinstance(opts[1], dict) else opts[1]
            poll_html = f"""
        <div class="rounded-xl bg-gray-50 border border-gray-200 p-6 mb-6 text-center">
          <p class="font-semibold text-gray-700 mb-4">{pq}</p>
          <div class="flex gap-4 justify-center flex-wrap">
            <span class="px-6 py-2 rounded-full bg-red-100 text-red-700 font-medium">{opt0}</span>
            <span class="px-6 py-2 rounded-full bg-blue-100 text-blue-700 font-medium">{opt1}</span>
          </div>
          <p class="text-xs text-gray-400 mt-3">Vote on the full story at <a href="https://www.redwhiteandskewed.com" class="underline">redwhiteandskewed.com</a></p>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} | Red, White, and Skewed</title>
  <meta name="description" content="{description[:200]}">
  <link rel="canonical" href="{page_url}">
  <link rel="alternate" type="application/rss+xml" title="Red, White, and Skewed" href="https://www.redwhiteandskewed.com/feed.xml">

  <!-- Open Graph -->
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="Red, White, and Skewed">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{description[:200]}">
  <meta property="og:url" content="{page_url}">
  <meta property="og:image" content="{image_url or 'https://www.redwhiteandskewed.com/rws-social-share.png'}">
  <meta property="article:published_time" content="{slug[:10]}">

  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:site" content="@RedWhiteSkewed">
  <meta name="twitter:title" content="{title}">
  <meta name="twitter:description" content="{description[:200]}">
  <meta name="twitter:image" content="{image_url or 'https://www.redwhiteandskewed.com/rws-social-share.png'}">

  <!-- JSON-LD NewsArticle -->
  <script type="application/ld+json">
  {json.dumps(jsonld, indent=2)}
  </script>

  <!-- Google Analytics -->
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-DKYV79XGTK"></script>
  <script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag('js',new Date());gtag('config','G-DKYV79XGTK');</script>

  <!-- Google AdSense -->
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-8366110078658936" crossorigin="anonymous"></script>

  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    body {{ font-family: 'Georgia', serif; background: #faf9f7; color: #0d0d0d; }}
    a {{ color: inherit; }}
  </style>
</head>
<body class="min-h-screen">

  <!-- Header -->
  <header class="bg-gray-900 text-white py-4 px-6 text-center">
    <a href="https://www.redwhiteandskewed.com" class="text-2xl font-bold tracking-tight">
      Red, White, &amp; Skewed
    </a>
    <p class="text-gray-400 text-xs mt-1">The Same Story. Two Views. Zero Agreement.</p>
  </header>

  <main class="max-w-3xl mx-auto px-4 py-8">

    <!-- Date + title -->
    <p class="text-sm text-gray-500 mb-2">{date_str}</p>
    <h1 class="text-3xl font-bold leading-tight mb-3">{title}</h1>
    {f'<p class="text-lg text-gray-600 mb-6 leading-relaxed">{subtitle}</p>' if subtitle else ''}

    {image_html}
    {poll_html}
    {con_html}
    {lib_html}
    {factcheck_html}

    <!-- Back link -->
    <div class="mt-8 pt-6 border-t border-gray-200 text-center">
      <a href="https://www.redwhiteandskewed.com" class="text-blue-600 underline text-sm">← Back to today's story</a>
      &nbsp;&nbsp;
      <a href="https://www.redwhiteandskewed.com/archive.html" class="text-blue-600 underline text-sm">Browse all stories →</a>
    </div>

  </main>

  <footer class="text-center text-xs text-gray-400 py-8">
    &copy; {slug[:4]} Red, White, and Skewed &bull;
    <a href="https://www.redwhiteandskewed.com/privacy.html" class="underline">Privacy</a>
  </footer>

</body>
</html>"""

    out_dir = pathlib.Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{slug}.html"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    return out_path


def generate_all_story_pages(story_files):
    """Generate a static HTML page for every story."""
    out_dir = SCRIPT_DIR / "stories"
    count = 0
    for slug, filepath in story_files:
        story = load_story(filepath)
        if not story:
            continue
        generate_story_page(slug, story, out_dir)
        count += 1
    print(f"Generated {count} story pages in stories/")
    return out_dir


def main():
    print("RWS SEO Generator")
    print("=" * 50)

    story_files = get_story_files()
    print(f"Found {len(story_files)} story files")

    generate_sitemap(story_files)
    generate_rss(story_files)
    generate_all_story_pages(story_files)

    print("=" * 50)
    print("Done. Files generated:")
    print("  sitemap.xml")
    print("  feed.xml")
    print(f"  stories/*.html ({len(story_files)} pages)")


if __name__ == "__main__":
    main()
