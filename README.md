# Weather Network Pollen Scraper (Home Assistant Add-on)
# Proof of concept

This Home Assistant add-on scrapes pollen levels, top allergens, and a 3‑day forecast from The Weather Network using Browserless + Pyppeteer.  
It is designed for HAOS and runs as a long‑lived service, updating pollen data multiple times per day.

## Features

- Scrapes today's pollen level
- Extracts top allergens
- Extracts 3‑day pollen forecast (via SVG color decoding)
- Uses Browserless for reliable DOM rendering
- Configurable scrape frequency (0–4 times per day)
- Debug mode for troubleshooting (HTML + screenshots)
- Outputs JSON to `/share/pollen/pollen_data.json`

## Installation

1. Add this repository to Home Assistant:
   - **Settings → Add-ons → Add-on Store → ⋮ → Repositories**
   - Add:  
     `https://github.com/YOUR_GITHUB_USERNAME/twn-pollen-scraper-addon`

2. Install **Weather Network Pollen Scraper** from the Add-on Store.

3. Configure options:
   - Pollen URL
   - Scrapes per day
   - Browserless URL
   - Debug mode

4. Start the add-on.

## Output

The scraper writes:
/share/pollen/pollen_data.json


Example:

```json
{
  "today": { "level": "High", "top_allergens": ["Birch", "Poplar"] },
  "forecast": [
    { "day": "Sun 26", "level": "High" },
    { "day": "Mon 27", "level": "Very High" },
    { "day": "Tue 28", "level": "Very High" }
  ]
}

