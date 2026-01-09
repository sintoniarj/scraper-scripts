#!/bin/bash
# Bootstrap script for scraper
# This script downloads the scraper from GitHub and runs it

set -e

REPO_URL="https://raw.githubusercontent.com/manus-scraper/scraper-scripts/main"
WORK_DIR="/tmp/scraper-work"

echo "=== Scraper Bootstrap ==="
echo "Target URL: $TARGET_URL"
echo "Job ID: $JOB_ID"
echo "Max Pages: ${MAX_PAGES:-10}"

# Create work directory
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

# Download scraper script
echo "Downloading scraper..."
curl -sL "${REPO_URL}/scraper.py" -o scraper.py

# Check if download was successful
if [ ! -f scraper.py ]; then
    echo '{"status": "error", "message": "Failed to download scraper script"}'
    exit 1
fi

echo "Scraper downloaded successfully"

# Run the scraper
echo "Starting scraper..."
python3 scraper.py
