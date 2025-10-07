from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from db.connection import execute_query
import json
import time

#  playwright install chromium
# PYPPETEER_EXECUTABLE_PATH =  r"C:\Users\Marco\AppData\Local\ms-playwright\chromium-1187"





def get_html(url):
    """Fetch and render HTML via Playwright (headless Chromium)."""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_default_timeout(20000)
            page.goto(url)

            # Wait for something meaningful to load
            # (you can tweak the selector depending on site)
            page.wait_for_load_state("networkidle")

            html = page.content()
            browser.close()

        soup = BeautifulSoup(html, "html.parser")
        print(f"✅ Loaded (rendered): {url} | Title: {soup.title.string.strip() if soup.title else 'No title'}")
        return soup

    except Exception as e:
        print(f"⚠️ Failed to load {url}: {e}")
        return None


def fetch_url():
    rows = execute_query("SELECT TOP 1 model_id, spec_url FROM MotorcycleModels ORDER BY NEWID()")
    model_id, model_url = rows[0]
    return model_id, model_url


def get_ldjson(soup):
    scripts = soup.find_all("script", type="application/ld+json")
    for s in scripts:
        content = s.string
        if not content:
            continue
        if '"@type":"Motorcycle"' in content or '"@type": "Motorcycle"' in content:
            try:
                motorcycle_data = json.loads(content)
                brand = motorcycle_data.get("brand", {}).get("name")
                return brand, motorcycle_data
            except json.JSONDecodeError:
                continue
    return None, None


def scrape_url():
    """Fetch and parse dynamic content with Playwright."""
    for _ in range(15):
        byke_id, byke_url = fetch_url()
        soup = get_html(byke_url)
        if not soup:
            continue

        table = soup.find(id="GENERAL")
        if not table:
            print(f"⚠️ No GENERAL section found for {byke_url}")
            continue

        table = table.find_parent("table")
        specs = []
        section_desc = ""
        section_id = ""

        for row in table.find_all("tr"):
            if row.th:
                section_desc = row.th.get_text(strip=True)
                div = row.th.find("div")
                section_id = div.get("id") if div else section_desc

            cells = row.find_all("td")
            if cells and len(cells) == 2:
                label = cells[0].text.strip()
                text = cells[1].text.strip()

                if text.lower() == "loading..":
                    print(f"⏳ Waiting for {label} to finish loading...")
                    time.sleep(2)
                    soup = get_html(byke_url)
                    cells = soup.find(id="GENERAL").find_parent("table").find_all("td")
                    text = cells[1].text.strip() if cells else text

                specs.append((section_id, section_desc, label, text))
                specs.append({
                    "section_id": section_id,
                    "section_desc": section_desc,
                    "label": label,
                    "text": text,
                })


        brand, motorcycle_json = get_ldjson(soup)

        byke = {
            "byke_id": byke_id,
            "brand": brand,
        }

        # insert_byke_specs(byke, specs)
        #sql = "INSERT INTO MotorcycleModelsDetails (byke_id, brand, section_id, section_desc, label, text) VALUES (?, ?, ?, ?, ?, ?)"

if __name__ == "__main__":
    scrape_url()
