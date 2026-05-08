import asyncio
import json
import logging
import os
from datetime import datetime, timedelta

import time
import paho.mqtt.client as mqtt
from pyppeteer import connect

# -----------------------------
# Environment Variables. 
# -----------------------------
POLLEN_URL = os.getenv("POLLEN_URL")
BROWSERLESS_URL = os.getenv("BROWSERLESS_URL")
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"

MQTT_HOST = os.getenv("MQTT_HOST")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
MQTT_BASE = os.getenv("MQTT_BASE_TOPIC", "home/pollen")

DEVICE_NAME = "TWN Pollen"
DEVICE_ID = "twn_pollen_device"

CAPTURE_DIR = "/share/pollen/debug"

# -----------------------------
# LOGGER Setup
# -----------------------------
logging.basicConfig(
    level=logging.INFO,
    format=f"%(asctime)s - [v{VERSION}] - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

if DEBUG_MODE:
    logger.setLevel(logging.DEBUG)
    logger.debug("Debug mode enabled: Detailed logs will be shown.")
    os.makedirs(CAPTURE_DIR, exist_ok=True)
else:
    logger.setLevel(logging.INFO)

# -----------------------------
# MQTT Setup
# -----------------------------
def mqtt_connect():
    logger.debug("Connecting to MQTT.")
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1) # Adding forced V1 api until additionnal changes are in place

    if MQTT_USERNAME:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    client.connect(MQTT_HOST, MQTT_PORT, 60)
    return client

# -----------------------------
# MQTT Auto-Discovery
# -----------------------------
def publish_discovery(client, sensor_id, name, unit=None, icon=None):
    logger.debug("Publishing autodiscovery to MQTT.")
    topic = f"homeassistant/sensor/{DEVICE_ID}/{sensor_id}/config"

    payload = {
        "name": name,
        "state_topic": f"{MQTT_BASE}/{sensor_id}",
        "unique_id": f"{DEVICE_ID}_{sensor_id}",
        "device": {
            "identifiers": [DEVICE_ID],
            "name": DEVICE_NAME,
            "manufacturer": "The Weather Network",
            "model": "Pollen Index Scraper"
        }
    }

    if unit:
        payload["unit_of_measurement"] = unit
    if icon:
        payload["icon"] = icon

    client.publish(topic, json.dumps(payload), retain=True)


def publish_value(client, sensor_id, value):
    logger.debug("Publishing values to MQTT.")
    topic = f"{MQTT_BASE}/{sensor_id}"
    client.publish(topic, value, retain=True)


# -----------------------------
# Scoring Logic (0–5)
# -----------------------------
SCORE_MAP = {
    "None": 1,
    "Low": 2,
    "Moderate": 3,
    "High": 4,
    "Very High": 5
}


def score_from_level(level):
    if not level:
        logger.debug("Using default value for pollen level.")
        return 0
    return SCORE_MAP.get(level, 0)


# -----------------------------
# Scraper Logic
# -----------------------------
async def scrape_pollen():
    logger.info("Connecting to Browserless at {BROWSERLESS_URL}…")

    browser = await connect({
        "browserWSEndpoint": BROWSERLESS_URL,
        "defaultViewport": {"width": 1400, "height": 900}
    })

    page = await browser.newPage()
    page.setDefaultNavigationTimeout(90000)
    logger.info("Loading page and capturing information…")
    logger.debug(Loading page: {POLLEN_URL}")
    await page.goto(POLLEN_URL, {"waitUntil": "domcontentloaded"})

    await asyncio.sleep(5)
    await page.evaluate("window.scrollTo(0, 400);")
    await asyncio.sleep(2)
    await page.evaluate("window.scrollTo(0, 0);")
    await asyncio.sleep(2)

    logger.debug("Waiting for pollen summary widget…")
    await page.waitForSelector('[data-testid="aerobiology-pollen-daily-summary"]', timeout=20000)

    logger.debug("Waiting for 3-day forecast chart…")
    await page.waitForSelector('[data-testid="pollen-forecast-chart"]', timeout=20000)

    # Today's level
    logger.debug("Waiting for today's level")
    today_level = await page.querySelectorEval(
        '[data-testid="pollen-index-meter"] span',
        'el => el.textContent.trim()'
    )

    # Top allergens
    logger.debug("Waiting for allergens")
    top_allergens = await page.querySelectorAllEval(
        '[data-testid="top-allergens"] li',
        'els => els.map(el => el.textContent.trim())'
    )

    # Forecast days
    logger.debug("Waiting for forecast")
    forecast_days = await page.evaluate("""
    () => {
        const root = document.querySelector('[data-testid="pollen-forecast-chart"]');
        if (!root) return [];

        const tspanNodes = root.querySelectorAll('tspan');
        const texts = Array.from(tspanNodes).map(n => n.textContent.trim()).filter(Boolean);

        const result = [];
        for (let t of texts) {
            if (/(Mon|Tue|Wed|Thu|Fri|Sat|Sun|Today|Tomorrow)/i.test(t)) {
                result.push({ day: t, level: null });
            }
        }
        return result.slice(0, 3);
    }
    """)

    # Forecast levels via SVG colors
    logger.debug("Capturing forecast")
    forecast_levels = await page.evaluate("""
    () => {
        const root = document.querySelector('[data-testid="pollen-forecast-chart"]');
        if (!root) return [];

        const paths = root.querySelectorAll('path[fill]');
        const colors = Array.from(paths).map(p => p.getAttribute('fill'));

        const map = {
            '#C6C4C0': 'No data',
            '#97D602': 'None',
            '#FDCD2E': 'Low',
            '#E98600': 'Moderate',
            '#DE3E2A': 'High',
            '#9161C9': 'Very High'
        };

        return colors
            .map(c => map[c] || null)
            .filter(v => v !== null)
            .slice(0, 3);
    }
    """)

    for i in range(min(len(forecast_days), len(forecast_levels))):
        forecast_days[i]["level"] = forecast_levels[i]

    if DEBUG_MODE:
        logger.debug("Debug mode enabled — saving screenshots + HTML")
        await page.screenshot(path=f"{CAPTURE_DIR}/viewport.png")
        await page.screenshot(path=f"{CAPTURE_DIR}/fullpage.png", fullPage=True)
        html = await page.content()
        with open(f"{CAPTURE_DIR}/page.html", "w", encoding="utf-8") as f:
            f.write(html)

    await browser.close()

    return today_level, top_allergens, forecast_days


# -----------------------------
# Main Execution
# -----------------------------
async def main():
    try:
        today_level, top_allergens, forecast = await scrape_pollen()
    except Exception as e:
        log(f"ERROR: {e}")
        return

    client = mqtt_connect()

    # Auto-discovery sensors
    publish_discovery(client, "today_level", "Pollen Today Level", icon="mdi:flower")
    publish_discovery(client, "today_score", "Pollen Today Score")

    for i in range(3):
        publish_discovery(client, f"forecast_{i+1}_level", f"Pollen Forecast {i+1} Level", icon="mdi:flower")
        publish_discovery(client, f"forecast_{i+1}_score", f"Pollen Forecast {i+1} Score")

    publish_discovery(client, "top_allergens", "Top Allergens", icon="mdi:biohazard")

    # Publish values
    publish_value(client, "today_level", today_level)
    publish_value(client, "today_score", score_from_level(today_level))

    for i, f in enumerate(forecast):
        publish_value(client, f"forecast_{i+1}_level", f["level"])
        publish_value(client, f"forecast_{i+1}_score", score_from_level(f["level"]))

    publish_value(client, "top_allergens", json.dumps(top_allergens))

    log("MQTT publish complete.")


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
