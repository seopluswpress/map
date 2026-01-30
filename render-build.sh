#!/usr/bin/env bash
# exit on error
set -o errexit

# Upgrade pip
pip install --upgrade pip

# Install python dependencies
pip install -r requirements.txt

# Install Playwright and its system dependencies
# Note: We use the 'python -m' to ensure it uses the correct environment
python -m playwright install chromium
