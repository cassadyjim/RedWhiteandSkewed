#!/usr/bin/env python3
"""
Red White & Skewed - Local QA Test Server
==========================================
Serves the site locally so you can QA any story before publishing.

Usage:
    python3 rws_test_server.py                          # Loads latest.json
    python3 rws_test_server.py 2026-02-05-trump-nationalize-elections

Then open: http://localhost:8080

Press Ctrl+C to stop the server.
"""

import sys
import os
import json
import shutil
import http.server
import socketserver
import urllib.parse
import urllib.request
from pathlib import Path

PORT = 8080
SCRIPT_DIR = Path(__file__).parent.resolve()


# ============================================================
# MOCK VOTE API
# Returns fake vote data so the poll UI renders correctly
# ============================================================

MOCK_VOTE_RESPONSE = {
    "success": True,
    "user_vote": None,
    "archived": False,
    "results": {
        "conservative": 42,
        "liberal": 58,
        "total": 100,
        "conservative_percent": 42,
        "liberal_percent": 58
    }
}


class RWSHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler that maps /stories/ to the local JSON files
    and mocks the /api/vote.php endpoint."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(SCRIPT_DIR), **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path   = parsed.path

        # Image proxy — fetches external images server-side to avoid
        # Chrome's ORB blocking of cross-origin images on localhost
        if path == '/image-proxy':
            params = urllib.parse.parse_qs(parsed.query)
            url = params.get('url', [''])[0]
            if not url:
                self.send_error(400, 'Missing url parameter')
                return
            try:
                req = urllib.request.Request(
                    url,
                    headers={'User-Agent': 'Mozilla/5.0 (RWS QA Server)'}
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    content_type = resp.headers.get('Content-Type', 'image/jpeg')
                    data = resp.read()
                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self.send_header('Content-Length', str(len(data)))
                self.send_header('Cache-Control', 'max-age=300')
                self.end_headers()
                self.wfile.write(data)
                print(f"  🖼️  Proxied image: {url[:60]}...")
            except Exception as e:
                print(f"  ⚠️  Image proxy failed: {e}")
                self.send_error(502, f'Image proxy failed: {e}')
            return

        # Mock vote API
        if path == '/api/vote.php':
            self._send_json(MOCK_VOTE_RESPONSE)
            return

        # Map /stories/filename.json  →  ./filename.json in SCRIPT_DIR
        # Also rewrites image URLs to use the local proxy (avoids ORB blocking)
        if path.startswith('/stories/'):
            filename = path[len('/stories/'):]
            local_path = SCRIPT_DIR / filename
            if local_path.exists():
                try:
                    story = json.loads(local_path.read_bytes())
                    if 'image' in story and 'url' in story['image']:
                        orig = story['image']['url']
                        story['image']['url'] = '/image-proxy?url=' + urllib.parse.quote(orig, safe='')
                    data = json.dumps(story).encode()
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Content-Length', str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                except Exception:
                    self._send_file(local_path, 'application/json')
            else:
                self.send_error(404, f"Story not found: {filename}")
            return

        # Everything else: serve from SCRIPT_DIR normally
        super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        # Mock vote POST
        if parsed.path == '/api/vote.php':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            try:
                data = json.loads(body)
                vote = data.get('vote', 'conservative')
            except Exception:
                vote = 'conservative'

            response = dict(MOCK_VOTE_RESPONSE)
            response['user_vote'] = vote
            self._send_json(response)
            return

        self.send_error(404)

    def _send_json(self, data):
        body = json.dumps(data).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path, content_type):
        data = path.read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format, *args):
        # Clean up log output
        msg = format % args
        if '404' in msg:
            print(f"  ⚠️  {msg}")
        elif '/api/vote' in msg:
            print(f"  🗳️  Vote API: {msg}")
        elif '.json' in msg:
            print(f"  📄 {msg}")
        # Suppress CSS/JS/font noise
        elif any(x in msg for x in ['.css', '.js', 'fonts.g', 'tailwind', 'gtag']):
            pass
        else:
            print(f"  →  {msg}")


# ============================================================
# SETUP: Determine which story to preview
# ============================================================

def setup_preview(story_slug=None):
    """
    If a story slug is given, temporarily point latest.json at that story.
    Otherwise just use the existing latest.json.
    Returns the story filename being previewed.
    """
    if not story_slug:
        latest = SCRIPT_DIR / 'latest.json'
        if latest.exists():
            try:
                data = json.loads(latest.read_text())
                return data.get('filename', 'latest.json')
            except Exception:
                pass
        return 'latest.json'

    # Find the JSON file
    if not story_slug.endswith('.json'):
        story_slug += '.json'

    story_path = SCRIPT_DIR / story_slug
    if not story_path.exists():
        print(f"❌ Story file not found: {story_slug}")
        print(f"   Looking in: {SCRIPT_DIR}")
        sys.exit(1)

    # Write a temporary latest.json pointing to this story
    story_data = json.loads(story_path.read_text())
    latest_path = SCRIPT_DIR / 'latest.json'

    # Back up existing latest.json if it exists
    backup_path = SCRIPT_DIR / 'latest.json.bak'
    if latest_path.exists() and not backup_path.exists():
        shutil.copy(latest_path, backup_path)
        print(f"  💾 Backed up existing latest.json → latest.json.bak")

    latest_path.write_text(json.dumps(story_data, indent=2))
    print(f"  📰 Previewing: {story_slug}")
    return story_slug


def restore_latest():
    """Restore latest.json.bak if it exists."""
    backup_path = SCRIPT_DIR / 'latest.json.bak'
    latest_path = SCRIPT_DIR / 'latest.json'
    if backup_path.exists():
        shutil.move(str(backup_path), str(latest_path))
        print(f"\n  ✅ Restored original latest.json")


# ============================================================
# MAIN
# ============================================================

def main():
    story_arg = sys.argv[1] if len(sys.argv) > 1 else None
    story_file = setup_preview(story_arg)

    print()
    print("=" * 60)
    print("  Red White & Skewed - Local QA Server")
    print("=" * 60)
    print(f"  Story   : {story_file}")
    print(f"  URL     : http://localhost:{PORT}")
    print(f"  Folder  : {SCRIPT_DIR}")
    print()
    print("  Open http://localhost:8080 in your browser")
    print("  Press Ctrl+C to stop")
    print("=" * 60)
    print()

    try:
        with socketserver.TCPServer(("", PORT), RWSHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    except OSError as e:
        if 'Address already in use' in str(e):
            print(f"\n❌ Port {PORT} is already in use.")
            print(f"   Kill the process using it, or change PORT in this script.")
        else:
            raise
    finally:
        restore_latest()
        print("  Server stopped.")


if __name__ == '__main__':
    main()
