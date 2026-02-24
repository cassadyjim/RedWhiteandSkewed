#!/usr/bin/env python3
"""
Red White & Skewed - Automated SFTP Upload Script
Uploads story files and site assets to one.com hosting

Usage:
    # Upload a specific story JSON
    python3 rws_upload.py --story path/to/story.json
    
    # Upload all site files
    python3 rws_upload.py --full
    
    # Test connection
    python3 rws_upload.py --test
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

try:
    import paramiko
except ImportError:
    print("Error: paramiko not installed. Run: pip3 install paramiko")
    sys.exit(1)

# ============================================
# CONFIGURATION
# ============================================

# SFTP Connection Details for redwhiteandskewed.com on One.com
SFTP_CONFIG = {
    'host': os.environ.get('RWS_SFTP_HOST', 'ssh.c2hdl62rf.service.one'),
    'port': int(os.environ.get('RWS_SFTP_PORT', 22)),
    'username': os.environ.get('RWS_SFTP_USERNAME', 'c2hdl62rf_ssh'),
    'password': os.environ.get('RWS_SFTP_PASSWORD', '4AFeB76RBuZe'),
}

# Remote paths on one.com (relative to connection root - which IS the web root)
REMOTE_PATHS = {
    'root': '/',
    'stories': '/stories/',
    'api': '/api/',
    'css': '/css/',
    'js': '/js/',
}

# Local paths (update to match your setup)
LOCAL_PATHS = {
    'stories': './stories/',
    'site': './',
}

# ============================================
# SFTP HELPER CLASS
# ============================================

class RWSUploader:
    def __init__(self, config):
        self.config = config
        self.sftp = None
        self.transport = None
        
    def connect(self):
        """Establish SFTP connection"""
        print(f"🔗 Connecting to {self.config['host']}...")
        
        try:
            self.transport = paramiko.Transport((self.config['host'], self.config['port']))
            self.transport.connect(
                username=self.config['username'],
                password=self.config['password']
            )
            self.sftp = paramiko.SFTPClient.from_transport(self.transport)
            
            # On One.com for redwhiteandskewed.com, web files are in webroots/d04b24ba/
            try:
                self.sftp.chdir('webroots/d04b24ba')
                print("✅ Connected successfully! (in web root)")
            except:
                print("✅ Connected successfully!")
            
            return True
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close SFTP connection"""
        if self.sftp:
            self.sftp.close()
        if self.transport:
            self.transport.close()
        print("🔌 Disconnected")
    
    def ensure_remote_dir(self, remote_path):
        """Create remote directory if it doesn't exist"""
        # Strip leading slash for relative path
        remote_path = remote_path.lstrip('/')
        
        if not remote_path:
            return
            
        dirs = remote_path.strip('/').split('/')
        current = ''
        
        for d in dirs:
            current = current + '/' + d if current else d
            try:
                self.sftp.stat(current)
                # Directory exists, continue
            except FileNotFoundError:
                try:
                    print(f"  📁 Creating directory: {current}")
                    self.sftp.mkdir(current)
                except IOError as e:
                    # Directory might exist or permission issue
                    pass
            except IOError:
                pass
    
    def upload_file(self, local_path, remote_path):
        """Upload a single file"""
        try:
            # Strip leading slash for relative path
            remote_path = remote_path.lstrip('/')
            
            # Ensure parent directory exists
            remote_dir = os.path.dirname(remote_path)
            if remote_dir:
                self.ensure_remote_dir(remote_dir)
            
            print(f"  📤 Uploading: {local_path} → {remote_path}")
            self.sftp.put(local_path, remote_path)
            print(f"  ✅ Success: {os.path.basename(remote_path)}")
            return True
            
        except FileNotFoundError as e:
            print(f"  ❌ Local file not found: {local_path}")
            return False
        except PermissionError as e:
            print(f"  ❌ Permission denied: {remote_path}")
            return False
        except IOError as e:
            print(f"  ❌ IO Error uploading {local_path}: {e}")
            return False
        except Exception as e:
            print(f"  ❌ Failed to upload {local_path}: {type(e).__name__}: {e}")
            return False
    
    def upload_story(self, story_json_path):
        """Upload a story JSON file and update latest.json and index.json"""
        if not os.path.exists(story_json_path):
            print(f"❌ Story file not found: {story_json_path}")
            return False
        
        filename = os.path.basename(story_json_path)
        remote_path = REMOTE_PATHS['stories'] + filename
        
        # Read the story to get metadata
        with open(story_json_path, 'r') as f:
            story_data = json.load(f)
        
        # Upload the story file
        success = self.upload_file(story_json_path, remote_path)
        
        if success:
            # Update latest.json by copying this story
            latest_remote = (REMOTE_PATHS['stories'] + 'latest.json').lstrip('/')
            print(f"  📤 Updating latest.json...")
            self.sftp.put(story_json_path, latest_remote)
            
            # Update index.json for archive
            index_remote = (REMOTE_PATHS['stories'] + 'index.json').lstrip('/')
            try:
                # Try to download existing index
                with self.sftp.open(index_remote, 'r') as f:
                    index_data = json.load(f)
            except:
                # Create new index if doesn't exist
                index_data = []
            
            # Mark all existing stories as archived
            for story in index_data:
                story['archived'] = True
            
            # Check if this story already exists in index
            existing = next((s for s in index_data if s['filename'] == filename), None)
            if existing:
                # Update existing entry
                existing['date'] = story_data.get('date', '')
                existing['title'] = story_data.get('title', '')
                existing['subtitle'] = story_data.get('subtitle', '')
                existing['archived'] = False  # Current story is not archived
            else:
                # Add new entry at the beginning
                new_entry = {
                    'filename': filename,
                    'date': story_data.get('date', ''),
                    'title': story_data.get('title', ''),
                    'subtitle': story_data.get('subtitle', ''),
                    'archived': False
                }
                index_data.insert(0, new_entry)
            
            # Upload updated index
            print(f"  📤 Updating index.json...")
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
                json.dump(index_data, tmp, indent=2)
                tmp_path = tmp.name
            self.sftp.put(tmp_path, index_remote)
            os.unlink(tmp_path)
            
            print(f"✅ Story uploaded and set as latest!")
        
        return success
    
    def upload_directory(self, local_dir, remote_dir, extensions=None):
        """Upload all files from a directory"""
        if not os.path.exists(local_dir):
            print(f"❌ Directory not found: {local_dir}")
            return 0
        
        uploaded = 0
        
        for root, dirs, files in os.walk(local_dir):
            for filename in files:
                # Filter by extension if specified
                if extensions:
                    ext = os.path.splitext(filename)[1].lower()
                    if ext not in extensions:
                        continue
                
                local_path = os.path.join(root, filename)
                
                # Calculate relative path
                rel_path = os.path.relpath(local_path, local_dir)
                remote_path = remote_dir.rstrip('/') + '/' + rel_path.replace('\\', '/')
                
                if self.upload_file(local_path, remote_path):
                    uploaded += 1
        
        return uploaded
    
    def upload_full_site(self, local_site_dir):
        """Upload all site files"""
        print("\n📦 Uploading full site...")
        
        total = 0
        root = REMOTE_PATHS['root'].rstrip('/')
        
        # HTML files to root
        for f in Path(local_site_dir).glob('*.html'):
            if self.upload_file(str(f), root + '/' + f.name):
                total += 1
        
        # Stories directory
        stories_dir = os.path.join(local_site_dir, 'stories')
        if os.path.exists(stories_dir):
            total += self.upload_directory(stories_dir, REMOTE_PATHS['stories'], extensions=['.json'])
        
        # API directory
        api_dir = os.path.join(local_site_dir, 'api')
        if os.path.exists(api_dir):
            total += self.upload_directory(api_dir, REMOTE_PATHS['api'], extensions=['.php'])
        
        # JS files
        for f in Path(local_site_dir).glob('*.js'):
            if self.upload_file(str(f), root + '/' + f.name):
                total += 1
        
        # CSS files
        for f in Path(local_site_dir).glob('*.css'):
            if self.upload_file(str(f), root + '/' + f.name):
                total += 1
        
        print(f"\n✅ Uploaded {total} files total")
        return total


# ============================================
# MAIN FUNCTIONS
# ============================================

def test_connection():
    """Test SFTP connection"""
    print("🧪 Testing SFTP connection...\n")
    
    uploader = RWSUploader(SFTP_CONFIG)
    
    if uploader.connect():
        print("\n📂 Web root contents:")
        try:
            for item in uploader.sftp.listdir('.')[:20]:
                print(f"   {item}")
        except Exception as e:
            print(f"   Error listing: {e}")
        
        uploader.disconnect()
        return True
    
    return False


def upload_story(story_path):
    """Upload a single story"""
    print(f"📰 Uploading story: {story_path}\n")
    
    uploader = RWSUploader(SFTP_CONFIG)
    
    if not uploader.connect():
        return False
    
    success = uploader.upload_story(story_path)
    uploader.disconnect()
    
    return success


def upload_full_site(site_dir):
    """Upload all site files"""
    print(f"🌐 Uploading full site from: {site_dir}\n")
    
    uploader = RWSUploader(SFTP_CONFIG)
    
    if not uploader.connect():
        return False
    
    count = uploader.upload_full_site(site_dir)
    uploader.disconnect()
    
    return count > 0


def upload_api():
    """Upload just the API files"""
    print("🔧 Uploading API files...\n")
    
    uploader = RWSUploader(SFTP_CONFIG)
    
    if not uploader.connect():
        return False
    
    # Upload vote API to httpd.www/api/
    api_files = [
        ('vote_api.php', REMOTE_PATHS['api'] + 'vote.php'),
    ]
    
    for local, remote in api_files:
        if os.path.exists(local):
            uploader.upload_file(local, remote)
    
    uploader.disconnect()
    return True


def upload_single_file(file_path):
    """Upload a single file to web root"""
    print(f"📄 Uploading file: {file_path}\n")
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    uploader = RWSUploader(SFTP_CONFIG)
    
    if not uploader.connect():
        return False
    
    filename = os.path.basename(file_path)
    success = uploader.upload_file(file_path, filename)
    
    uploader.disconnect()
    return success


def upload_index(index_path):
    """Upload stories index.json file"""
    print(f"📋 Uploading stories index: {index_path}\n")
    
    if not os.path.exists(index_path):
        print(f"❌ File not found: {index_path}")
        return False
    
    uploader = RWSUploader(SFTP_CONFIG)
    
    if not uploader.connect():
        return False
    
    remote_path = REMOTE_PATHS['stories'] + 'index.json'
    success = uploader.upload_file(index_path, remote_path)
    
    uploader.disconnect()
    return success


# ============================================
# CLI INTERFACE
# ============================================

def main():
    parser = argparse.ArgumentParser(
        description='Red White & Skewed - SFTP Upload Utility',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 rws_upload.py --test                    # Test connection
  python3 rws_upload.py --story story.json        # Upload single story
  python3 rws_upload.py --full ./site             # Upload full site
  python3 rws_upload.py --api                     # Upload API files only
  
Environment Variables:
  RWS_SFTP_HOST      - SFTP hostname (default: ssh.redwhiteandskewed.com)
  RWS_SFTP_PORT      - SFTP port (default: 22)
  RWS_SFTP_USERNAME  - SFTP username (default: redwhiteandskewed.com)
  RWS_SFTP_PASSWORD  - SFTP password (required)
        """
    )
    
    parser.add_argument('--test', action='store_true', help='Test SFTP connection')
    parser.add_argument('--story', type=str, help='Upload a story JSON file')
    parser.add_argument('--file', type=str, help='Upload any single file to web root')
    parser.add_argument('--index', type=str, help='Upload stories index.json file')
    parser.add_argument('--full', type=str, nargs='?', const='./', help='Upload full site from directory')
    parser.add_argument('--api', action='store_true', help='Upload API files only')
    
    args = parser.parse_args()
    
    # Check password is set
    if not SFTP_CONFIG['password'] and not args.test:
        print("❌ SFTP password not set!")
        print("   Set RWS_SFTP_PASSWORD environment variable or update the script.")
        sys.exit(1)
    
    print("=" * 50)
    print("  Red White & Skewed - Upload Utility")
    print("=" * 50)
    print(f"  Host: {SFTP_CONFIG['host']}")
    print(f"  User: {SFTP_CONFIG['username']}")
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    if args.test:
        success = test_connection()
    elif args.story:
        success = upload_story(args.story)
    elif args.file:
        success = upload_single_file(args.file)
    elif args.index:
        success = upload_index(args.index)
    elif args.full is not None:
        success = upload_full_site(args.full)
    elif args.api:
        success = upload_api()
    else:
        parser.print_help()
        sys.exit(0)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
