import requests
from bs4 import BeautifulSoup
from db.connection import execute_query
import json

def get_html(url):
    """Fetches and parses an HTML page into a BeautifulSoup object."""
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()  # raises an HTTPError if the request failed

    soup = BeautifulSoup(resp.text, "html.parser")
    print(f"✅ Loaded: {resp.url} | Title: {soup.title.string.strip() if soup.title else 'No title'}")
    return soup

def fetch_url():
    rows = execute_query("SELECT TOP 1 model_id, model_url FROM MotorcycleModels ORDER BY NEWID()")
    model_id, model_url = rows[0]
    return  model_id, model_url

def get_ldjson(soup):
    scripts = soup.find_all("script", type="application/ld+json")

    motorcycle_data = None

    for s in scripts:
        content = s.string
        if not content:
            continue

        if '"@type":"Motorcycle"' in content or '"@type": "Motorcycle"' in content:
            try:
                motorcycle_data = json.loads(content)
                brand = motorcycle_data.get("brand").get("name")
                return brand, motorcycle_data
            except json.JSONDecodeError:
                # Sometimes JSON-LD may contain comments or invalid JSON — handle gracefully
                continue
    return None


# ---- Scraper ----

def scrape_url():
    """Fetch a URL asynchronously and return parsed data"""
    n = 0
    while n <5:
        byke_id, byke_url = fetch_url()
        soup = get_html(byke_url)

        table = soup.find(id="GENERAL").find_parent("table")
        specs = []
        section_desc = ""
        section_id = ""
        for row in table.find_all("tr"):
            if row.th:
                section_desc = row.th.get_text(strip=True)
                section_id = row.th.find("div").get("id")

            cells = row.find_all("td")
            if cells and len(cells) == 2:
                label = cells[0].text.strip()
                text = cells[1].text.strip()
                specs.append((section_id,section_desc, label, text))

        brand, motorcycle_json = get_ldjson(soup)


        for section_desc,section_id, label, text in specs:
            print(f"{brand} -ID:{byke_id}. {section_desc} ({section_id}) - {label}: {text}")

        n+=1



scrape_url()