#!/usr/bin/env python3
"""
generate_archive_index.py

Scans the /stories/ folder for JSON story files and generates index.json
for the Red, White, and Skewed archive page.

Usage:
    python generate_archive_index.py

    Or specify a custom path:
    python generate_archive_index.py --stories-dir /path/to/stories

File naming convention expected: YYYY-MM-DD-slug-here.json
Example: 2026-01-18-trump-greenland-tariffs-nato-allies.json
"""

import json
import os
import re
import argparse
from datetime import datetime
from pathlib import Path


def parse_date_from_filename(filename):
    """Extract date from filename like 2026-01-18-trump-greenland.json"""
    match = re.match(r'^(\d{4})-(\d{2})-(\d{2})-', filename)
    if match:
        year, month, day = match.groups()
        try:
            return datetime(int(year), int(month), int(day))
        except ValueError:
            return None
    return None


def format_date_display(dt):
    """Format date as 'January 18, 2026'"""
    return dt.strftime('%B %d, %Y').replace(' 0', ' ')  # Remove leading zero from day


def extract_story_metadata(filepath):
    """Extract title and subtitle from a story JSON file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return {
            'title': data.get('title', 'Untitled Story'),
            'subtitle': data.get('subtitle', ''),
            'date_from_json': data.get('date', '')
        }
    except (json.JSONDecodeError, IOError) as e:
        print(f"  Warning: Could not read {filepath}: {e}")
        return None


def generate_index(stories_dir, output_file=None):
    """Generate the index.json file from story files"""
    
    stories_path = Path(stories_dir)
    
    if not stories_path.exists():
        print(f"Error: Stories directory not found: {stories_dir}")
        return False
    
    if output_file is None:
        output_file = stories_path / 'index.json'
    
    print(f"Scanning: {stories_path}")
    print("-" * 50)
    
    stories = []
    
    # Find all JSON files matching the date pattern
    for filepath in sorted(stories_path.glob('*.json')):
        filename = filepath.name
        
        # Skip index.json itself
        if filename == 'index.json':
            continue
        
        # Parse date from filename
        file_date = parse_date_from_filename(filename)
        if not file_date:
            print(f"  Skipping (no date pattern): {filename}")
            continue
        
        # Extract metadata from file
        metadata = extract_story_metadata(filepath)
        if not metadata:
            continue
        
        # Use date from JSON if available, otherwise from filename
        display_date = metadata['date_from_json'] or format_date_display(file_date)
        
        story_entry = {
            'filename': filename,
            'date': display_date,
            'title': metadata['title'],
            'subtitle': metadata['subtitle'],
            'type': 'json',
            'path': '/stories/',
            'archived': False,
            '_sort_date': file_date.isoformat()  # For sorting
        }
        
        stories.append(story_entry)
        print(f"  Added: {filename}")
        print(f"         → {metadata['title'][:50]}...")
    
    if not stories:
        print("\nNo stories found!")
        return False
    
    # Sort by date (newest first)
    stories.sort(key=lambda x: x['_sort_date'], reverse=True)
    
    # Mark all but the first as archived
    for i, story in enumerate(stories):
        story['archived'] = (i > 0)
        del story['_sort_date']  # Remove sort helper
    
    # Write index.json
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(stories, f, indent=2, ensure_ascii=False)
    
    print("-" * 50)
    print(f"Generated: {output_file}")
    print(f"Total stories: {len(stories)}")
    print(f"Latest: {stories[0]['title'][:50]}...")
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description='Generate archive index.json for Red, White, and Skewed'
    )
    parser.add_argument(
        '--stories-dir',
        default='./stories',
        help='Path to stories directory (default: ./stories)'
    )
    parser.add_argument(
        '--output',
        default=None,
        help='Output file path (default: {stories-dir}/index.json)'
    )
    
    args = parser.parse_args()
    
    success = generate_index(args.stories_dir, args.output)
    exit(0 if success else 1)


if __name__ == '__main__':
    main()
