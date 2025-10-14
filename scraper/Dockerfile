FROM python:3.11-slim

# --- prerequisites first (ca-certificates BEFORE curl to validate TLS)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates curl gnupg apt-transport-https && \
    update-ca-certificates

# --- add Microsoft repo using signed keyring (no apt-key)
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc \
    | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg && \
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" \
    > /etc/apt/sources.list.d/microsoft-prod.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18 unixodbc-dev build-essential && \
    rm -rf /var/lib/apt/lists/*


# ensure playwright downloads browsers into the image (not at runtime)
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r scraper_reqs.txt

# Install Playwright browsers + all OS deps for headless Chromium
# (this pulls ~120–200 MB)
RUN python -m playwright install --with-deps chromium

COPY app.py .
RUN mkdir -p /app/data

