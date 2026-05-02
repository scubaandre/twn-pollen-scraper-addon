import asyncio
from pyppeteer import connect
import json
import os
import time

# Read environment variables passed from run.sh
POLLEN_URL = os.getenv("POLLEN_URL")
BROWSERLESS_URL = os.getenv("BROWSERLESS_URL")
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"

OUTPUT_DIR = "/share/pollen"
CAPTURE_DIR = "/share/pollen/debug"

os.makedirs(OUTPUT_DIR, exist_ok=True)
if DEBUG_MODE:
    os.makedirs(CAPTURE_DIR, exist_ok=True)


def log(msg):
    ts = time.strftime("%H:%M:%S")
    print(f"[Pollen Scraper] {ts} {msg}")


async def scrape_pollen():
    log(f"Connecting to Browserless at {BROWSERLESS_URL}…")

    browser = await connect({
        "browserWSEndpoint": BROWSERLESS_URL,
        "defaultViewport": {"width": 1400, "height": 900}
    })

    page = await browser.newPage()
    page.setDefaultNavigationTimeout(90000)

    log(f"Loading page: {POLLEN_URL}")
    await page.goto(POLLEN_URL, {"waitUntil": "domcontentloaded"})

    # Allow React hydration
    await asyncio.sleep(5)

    # Trigger lazy components
    await page.evaluate("window.scrollTo(0, 400);")
    await asyncio.sleep(2)
    await page.evaluate("window.scrollTo(0, 0);")
    await asyncio.sleep(2)

    # Wait for widgets
    log("Waiting for pollen summary widget…")
    await page.waitForSelector('[data-testid="aerobiology-pollen-daily-summary"]', timeout=20000)

    log("Waiting for 3-day forecast chart…")
    await page.waitForSelector('[data-testid="pollen-forecast-chart"]', timeout=20000)

    # ---- TODAY'S POLLEN LEVEL ----
    today_level = await page.querySelectorEval(
        '[data-testid="pollen-index-meter"] span',
        'el => el.textContent.trim()'
    )

    # ---- TOP ALLERGENS ----
    top_allergens = await page.querySelectorAllEval(
        '[data-testid="top-allergens"] li',
        'els => els.map(el => el.textContent.trim())'
    )

    # ---- FORECAST DAY LABELS ----
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

    # ---- FORECAST LEVELS FROM SVG PATH COLORS ----
    forecast_levels = await page.evaluate("""
    () => {
        const root = document.querySelector('[data-testid="pollen-forecast-chart"]');
        if (!root) return [];

        const paths = root.querySelectorAll('path[fill]');
        const colors = Array.from(paths).map(p => p.getAttribute('fill'));

        const map = {
            '#00AEEF': 'Very Low',
            '#7CC576': 'Low',
            '#F7D154': 'Moderate',
            '#E86C4F': 'High',
            '#DE3E2A': 'High',
            '#9161C9': 'Very High'
        };

        return colors
            .map(c => map[c] || null)
            .filter(v => v !== null)
            .slice(0, 3);
    }
    """)

    # ---- MERGE DAYS + LEVELS ----
    for i in range(min(len(forecast_days), len(forecast_levels))):
        forecast_days[i]["level"] = forecast_levels[i]

    # ---- STRUCTURED RESULT ----
    data = {
        "today": {
            "level": today_level,
            "top_allergens": top_allergens,
        },
        "forecast": forecast_days,
        "source": "The Weather Network / Aerobiology Research",
        "url": POLLEN_URL,
        "timestamp": time.time()
    }

    # ---- SAVE OUTPUT ----
    output_path = f"{OUTPUT_DIR}/pollen_data.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    log(f"Saved pollen data → {output_path}")

    # ---- DEBUG ARTIFACTS ----
    if DEBUG_MODE:
        log("Debug mode enabled — saving HTML and screenshots…")
        await page.screenshot(path=f"{CAPTURE_DIR}/viewport.png")
        await page.screenshot(path=f"{CAPTURE_DIR}/fullpage.png", fullPage=True)

        html = await page.content()
        with open(f"{CAPTURE_DIR}/page.html", "w", encoding="utf-8") as f:
            f.write(html)

    await browser.close()
    return data


async def main():
    try:
        await scrape_pollen()
    except Exception as e:
        log(f"ERROR: {e}")


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
