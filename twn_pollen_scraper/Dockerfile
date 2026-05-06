FROM python:3.11-alpine3.18

LABEL \
  io.hass.name="Weather Network Pollen Scraper" \
  io.hass.version="0.2.3" \
  io.hass.type="addon"

# Install system dependencies
RUN apk add --no-cache \
    bash \
    jq \
    chromium \
    chromium-chromedriver \
    nss \
    freetype \
    harfbuzz \
    ttf-freefont

# Install Python dependencies
RUN pip install --no-cache-dir \
    pyppeteer \
    paho-mqtt

ENV PYTHONUNBUFFERED=1
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium-browser

WORKDIR /app

COPY twn_pollen_scraper.py .
COPY run.sh .
RUN chmod a+x run.sh

CMD [ "/bin/bash", "/app/run.sh" ]
