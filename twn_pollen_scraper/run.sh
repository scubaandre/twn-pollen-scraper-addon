#!/usr/bin/env bash

set -e

echo "[TWN Pollen] Starting Weather Network Pollen Scraper add-on..."

# Read options from Home Assistant
POLLEN_URL=$(bashio::config 'pollen_url')
SCRAPES_PER_DAY=$(bashio::config 'scrapes_per_day')
BROWSERLESS_URL=$(bashio::config 'browserless_url')
DEBUG_MODE=$(bashio::config 'debug_mode')

MQTT_HOST=$(bashio::config 'mqtt_host')
MQTT_PORT=$(bashio::config 'mqtt_port')
MQTT_USERNAME=$(bashio::config 'mqtt_username')
MQTT_PASSWORD=$(bashio::config 'mqtt_password')
MQTT_BASE_TOPIC=$(bashio::config 'mqtt_base_topic')

# Validate scrapes_per_day
if [[ "$SCRAPES_PER_DAY" -eq 0 ]]; then
    echo "[TWN Pollen] scrapes_per_day=0 → Scraper disabled. Exiting."
    sleep infinity
fi

# Calculate interval in seconds
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

# Export environment variables for Python
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
