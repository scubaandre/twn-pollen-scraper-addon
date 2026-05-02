#!/usr/bin/env bash

set -e

echo "[Pollen Scraper] Starting Weather Network Pollen Scraper add-on..."

# Read options from Home Assistant
POLLEN_URL=$(bashio::config 'pollen_url')
SCRAPES_PER_DAY=$(bashio::config 'scrapes_per_day')
BROWSERLESS_URL=$(bashio::config 'browserless_url')
DEBUG_MODE=$(bashio::config 'debug_mode')

# Validate scrapes_per_day
if [[ "$SCRAPES_PER_DAY" -eq 0 ]]; then
    echo "[Pollen Scraper] scrapes_per_day=0 → Scraper disabled. Exiting."
    sleep infinity
fi

# Calculate interval in seconds
INTERVAL_HOURS=$(echo "24 / $SCRAPES_PER_DAY" | bc -l)
INTERVAL_SECONDS=$(printf "%.0f" "$(echo "$INTERVAL_HOURS * 3600" | bc -l)")

echo "[Pollen Scraper] URL: $POLLEN_URL"
echo "[Pollen Scraper] Browserless: $BROWSERLESS_URL"
echo "[Pollen Scraper] Scraping $SCRAPES_PER_DAY times per day"
echo "[Pollen Scraper] Interval: $INTERVAL_HOURS hours ($INTERVAL_SECONDS seconds)"
echo "[Pollen Scraper] Debug mode: $DEBUG_MODE"

# Export environment variables for Python
export POLLEN_URL
export BROWSERLESS_URL
export DEBUG_MODE

# Ensure output directory exists
mkdir -p /share/pollen

# Main loop
while true; do
    echo "[Pollen Scraper] Running pollen scraper at $(date)"

    python3 /app/twn_pollen_scraper.py

    if [[ $? -eq 0 ]]; then
        echo "[Pollen Scraper] Scrape completed successfully."
    else
        echo "[Pollen Scraper] ERROR: Scraper failed."
    fi

    echo "[Pollen Scraper] Sleeping for $INTERVAL_SECONDS seconds..."
    sleep "$INTERVAL_SECONDS"
done
