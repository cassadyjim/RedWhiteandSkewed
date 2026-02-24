#!/bin/bash
#
# Red White & Skewed - Publish Story
# One command to generate index + upload story + update site
#
# Usage:
#   ./rws_publish.sh story.json           # Publish a new story
#   ./rws_publish.sh --rebuild-index      # Just rebuild and upload index
#   ./rws_publish.sh --test               # Test SFTP connection
#
# Setup:
#   Place this script in your RWS project root alongside:
#   - rws_upload.py
#   - generate_archive_index.py
#   - stories/ folder
#

set -e  # Exit on any error

# ============================================
# CONFIGURATION
# ============================================

# Load credentials from .env file (never commit .env to git)
if [ -f "$( dirname "${BASH_SOURCE[0]}" )/.env" ]; then
    source "$( dirname "${BASH_SOURCE[0]}" )/.env"
else
    echo "❌ .env file not found. Copy .env.example to .env and add your credentials."
    exit 1
fi

# SFTP Credentials (loaded from .env)
export RWS_SFTP_HOST
export RWS_SFTP_USERNAME
export RWS_SFTP_PASSWORD

# Get script directory (where this script lives)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Stories are in the same directory as this script (not a subfolder)
STORIES_DIR="$SCRIPT_DIR"
# Index file goes in stories/ folder on the server, but we generate it locally first
INDEX_FILE="$SCRIPT_DIR/index.json"

# ============================================
# HELPER FUNCTIONS
# ============================================

print_header() {
    echo ""
    echo "=================================================="
    echo "  Red White & Skewed - Publisher"
    echo "=================================================="
    echo "  Time: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "=================================================="
    echo ""
}

check_dependencies() {
    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python3 not found. Please install Python."
        exit 1
    fi

    # Check paramiko
    python3 -c "import paramiko" 2>/dev/null || {
        echo "📦 Installing paramiko..."
        pip3 install paramiko
    }

    # Check required scripts exist
    if [ ! -f "$SCRIPT_DIR/rws_upload.py" ]; then
        echo "❌ rws_upload.py not found in $SCRIPT_DIR"
        exit 1
    fi

    if [ ! -f "$SCRIPT_DIR/generate_archive_index.py" ]; then
        echo "❌ generate_archive_index.py not found in $SCRIPT_DIR"
        exit 1
    fi
}

generate_index() {
    echo "📋 Generating archive index..."
    echo ""
    python3 "$SCRIPT_DIR/generate_archive_index.py" --stories-dir "$STORIES_DIR"
    echo ""
}

upload_index() {
    echo "📤 Uploading index.json..."
    python3 "$SCRIPT_DIR/rws_upload.py" --index "$INDEX_FILE"
    echo ""
}

upload_story() {
    local story_file="$1"
    echo "📰 Uploading story: $story_file"
    python3 "$SCRIPT_DIR/rws_upload.py" --story "$story_file"
    echo ""
}

test_connection() {
    echo "🧪 Testing SFTP connection..."
    python3 "$SCRIPT_DIR/rws_upload.py" --test
}

# ============================================
# MAIN
# ============================================

print_header
check_dependencies

case "$1" in
    --test)
        test_connection
        ;;
    
    --rebuild-index)
        echo "🔄 Rebuilding archive index only..."
        echo ""
        generate_index
        upload_index
        echo "✅ Index rebuilt and uploaded!"
        ;;
    
    "")
        echo "Usage:"
        echo "  ./rws_publish.sh STORY.json       Publish a new story"
        echo "  ./rws_publish.sh --rebuild-index  Rebuild and upload index only"
        echo "  ./rws_publish.sh --test           Test SFTP connection"
        echo ""
        echo "Example:"
        echo "  ./rws_publish.sh stories/2026-01-18-trump-greenland.json"
        ;;
    
    *)
        # Assume it's a story file
        STORY_FILE="$1"
        
        # Handle relative paths
        if [[ ! "$STORY_FILE" = /* ]]; then
            # If not absolute path, check if it exists as-is or in script dir
            if [ -f "$STORY_FILE" ]; then
                STORY_FILE="$(cd "$(dirname "$STORY_FILE")" && pwd)/$(basename "$STORY_FILE")"
            elif [ -f "$SCRIPT_DIR/$STORY_FILE" ]; then
                STORY_FILE="$SCRIPT_DIR/$STORY_FILE"
            fi
        fi
        
        # Verify file exists
        if [ ! -f "$STORY_FILE" ]; then
            echo "❌ Story file not found: $1"
            echo ""
            echo "Looked in:"
            echo "  - $1"
            echo "  - $SCRIPT_DIR/$1"
            exit 1
        fi
        
        # Get just the filename
        STORY_FILENAME=$(basename "$STORY_FILE")
        
        echo "🚀 Publishing: $STORY_FILENAME"
        echo ""
        
        # Step 1: Generate fresh index
        generate_index
        
        # Step 2: Upload the story (this also updates latest.json)
        upload_story "$STORY_FILE"
        
        # Step 3: Upload the regenerated index
        upload_index
        
        echo "=================================================="
        echo "  ✅ PUBLISHED SUCCESSFULLY!"
        echo "=================================================="
        echo ""
        echo "  Story:   https://redwhiteandskewed.com/?story=${STORY_FILENAME%.json}"
        echo "  Archive: https://redwhiteandskewed.com/archive.html"
        echo ""
        ;;
esac
