#!/bin/bash
#
# Red White & Skewed - Upload Script
# Run this from Terminal on your Mac
#
# Usage:
#   ./rws_upload.sh test              # Test connection
#   ./rws_upload.sh story FILE.json   # Upload a story
#   ./rws_upload.sh full              # Upload entire site
#   ./rws_upload.sh api               # Upload API files only
#

# SFTP Credentials (already configured)
export RWS_SFTP_HOST="ssh.c2hdl62rf.service.one"
export RWS_SFTP_USERNAME="c2hdl62rf_ssh"
export RWS_SFTP_PASSWORD="4AFeB76RBuZe"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

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

# Run the upload script
case "$1" in
    test)
        python3 "$SCRIPT_DIR/rws_upload.py" --test
        ;;
    story)
        if [ -z "$2" ]; then
            echo "❌ Usage: ./rws_upload.sh story FILE.json"
            exit 1
        fi
        python3 "$SCRIPT_DIR/rws_upload.py" --story "$2"
        ;;
    full)
        python3 "$SCRIPT_DIR/rws_upload.py" --full "${2:-.}"
        ;;
    api)
        python3 "$SCRIPT_DIR/rws_upload.py" --api
        ;;
    *)
        echo "Red White & Skewed - Upload Utility"
        echo ""
        echo "Usage:"
        echo "  ./rws_upload.sh test              Test SFTP connection"
        echo "  ./rws_upload.sh story FILE.json   Upload a story JSON"
        echo "  ./rws_upload.sh full [DIR]        Upload full site"
        echo "  ./rws_upload.sh api               Upload API files"
        ;;
esac
