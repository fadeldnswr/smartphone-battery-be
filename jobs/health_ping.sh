#!/bin/bash
# Simple health check for FastAPI

touch "$LOG_FILE"
chmod 664 "$LOG_FILE"

API_URL="http://103.103.21.2:8000/"
LOG_FILE="/home/fadeldnswr/smartphone-battery-be/jobs/health_ping.log"

TS="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL")

if [ "$HTTP_CODE" = "200" ]; then
  echo "$TS OK - FastAPI is up" >> "$LOG_FILE"
else
  echo "$TS ERROR - FastAPI returned $HTTP_CODE" >> "$LOG_FILE"
fi


