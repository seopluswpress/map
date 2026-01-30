#!/usr/bin/env bash
# exit on error
set -o errexit

# 1. Update pip
pip install --upgrade pip

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Install Playwright browser binaries
# We do NOT use --with-deps here because Render doesn't allow sudo.
# Render's native environment usually has most basic deps already.
python -m playwright install chromium

# 4. Final Crawl4AI setup
crawl4ai-setup
