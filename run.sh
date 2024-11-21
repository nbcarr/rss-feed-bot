#!/bin/bash

LOG_FILE="logs/rss-feed-bot_$(date '+%Y-%m-%d_%H-%M-%S').log"
SCRIPT_NAME="main.py"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

cd /home/ubuntu/rss-feed-bot || { log "Failed to navigate to project directory"; exit 1; }

log "Checking for updates and pulling from git repository..."
git pull origin main || { log "Failed to pull updates from git"; }

if [ ! -d "venv" ]; then
    log "Creating virtual environment..."
    python3 -m venv venv || { log "Failed to create virtual environment"; exit 1; }
fi

log "Activating virtual environment..."
source venv/bin/activate || { log "Failed to activate virtual environment"; exit 1; }

log "Upgrading pip..."
pip install --upgrade pip || log "Failed to upgrade pip, continuing..."

log "Installing requirements..."
pip install -r requirements.txt || { log "Failed to install requirements"; exit 1; }

log "Running $SCRIPT_NAME..."
python "$SCRIPT_NAME" 2>&1 | tee -a "$LOG_FILE"

deactivate

log "Script execution completed."