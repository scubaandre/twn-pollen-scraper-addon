#!/usr/bin/env bash

set -e

echo "[TWN Pollen] Starting Weather Network Pollen Scraper add-on..."

# Read config from /data/options.json
POLLEN_URL=$(jq -r '.pollen_url' /data/options.json)
SCRAPES_PER_DAY=$(jq -r '.scrapes_per_day' /data/options.json)
BROWSERLESS_URL=$(jq -r '.browserless_url' /data/options.json)
DEBUG_MODE=$(jq -r '.debug_mode' /data/options.json)

MQTT_HOST=$(jq -r '.mqtt_host' /data/options.json)
MQTT_PORT=$(jq -r '.mqtt_port' /data/options.json)
MQTT_USERNAME=$(jq -r '.mqtt_username' /data/options.json)
MQTT_PASSWORD=$(jq -r '.mqtt_password' /data/options.json)
MQTT_BASE_TOPIC=$(jq -r '.mqtt_base_topic' /data/options.json)

# Validate scrapes_per_day
if [[ "$SCRAPES_PER_DAY" -eq 0 ]]; then
    echo "[TWN Pollen] scrapes_per_day=0 → Scraper disabled. Exiting."
    sleep infinity
fi

# Calculate interval
INTERVAL_HOURS=$(echo "24 / $SCRAPES_PER_DAY" | bc -l)
INTERVAL_SECONDS=$(printf "%.0f" "$(echo "$INTERVAL_HOURS * 3600" | bc -l)")

echo "[TWN Pollen] URL: $POLLEN_URL"
echo "[TWN Pollen] Browserless: $BROWSERLESS_URL"
echo "[TWN Pollen] Scraping $SCRAPES_PER_DAY times per day"
echo "[TWN Pollen] Interval: $INTERVAL_HOURS hours ($INTERVAL_SECONDS seconds)"
echo "[TWN Pollen] Debug mode: $DEBUG_MODE"

echo "[TWN Pollen] MQTT Host: $MQTT_HOST"
echo "[TWN Pollen] MQTT Port: $MQTT_PORT"
echo "[TWN Pollen] MQTT Base Topic: $MQTT_BASE_TOPIC"

# Export env vars for Python
export POLLEN_URL
export BROWSERLESS_URL
export DEBUG_MODE

export MQTT_HOST
export MQTT_PORT
export MQTT_USERNAME
export MQTT_PASSWORD
export MQTT_BASE_TOPIC

# Main loop
while true; do
    echo "[TWN Pollen] Running pollen scraper at $(date)"

    python3 /app/twn_pollen_scraper.py

    if [[ $? -eq 0 ]]; then
        echo "[TWN Pollen] Scrape + MQTT publish completed successfully."
    else
        echo "[TWN Pollen] ERROR: Scraper failed."
    fi

    echo "[TWN Pollen] Sleeping for $INTERVAL_SECONDS seconds..."
    sleep "$INTERVAL_SECONDS"
done
