# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.2.3] - 2026-05-06

### Added
- Initial release of Weather Network Pollen Scraper add-on for Home Assistant
- Real-time pollen level scraping from The Weather Network
- Top allergen extraction
- 3-day pollen forecast with SVG color decoding
- MQTT integration for sensor data publishing
- Configurable scrape frequency (0-4 times per day)
- Debug mode for troubleshooting with HTML and screenshot outputs
- JSON data export to `/share/pollen/pollen_data.json`
- Browserless support for reliable DOM rendering
- Long-lived service architecture optimized for Home Assistant

### Technical Details
- Container built for Home Assistant compatibility
- Python 3.11 runtime on Alpine Linux
- Pyppeteer for headless browser automation
- MQTT client for sensor integration
- Configurable MQTT broker connection
