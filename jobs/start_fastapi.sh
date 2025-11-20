#!/bin/bash

# path project kamu
APP_DIR="/home/fadeldnswr/smartphone-battery-be"
VENV_DIR="$APP_DIR/.venv/bin/activate"
LOG_FILE="$APP_DIR/logs/fastapi.log"

# masuk ke folder project
cd "$APP_DIR" || exit 1

# aktifkan venv
source "$VENV_DIR"

# jalankan uvicorn di background + tulis log
# ganti src.main:app sesuai entrypoint kamu
nohup uvicorn src.main:app --host 0.0.0.0 --port 8000 >> "$LOG_FILE" 2>&1 &
