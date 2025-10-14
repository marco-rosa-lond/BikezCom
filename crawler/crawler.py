import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import sys
import pyodbc
from db_helper import insert_new_brand, insert_new_model, get_connection

# ------------------- DATABASE CONNECTION -------------------

cnxn = get_connection()
# cursor = cnxn.cursor()

# ------------------- CONSTANTS -------------------
BASE_URL = "https://bikez.com"
BRANDS_URL = f"{BASE_URL}/brands/index.php"
YEARS_URL = f"{BASE_URL}/years/index.php"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; BikezCrawler/1.0)"}


# ============================================================
#                   FETCH BRAND LIST
# ============================================================
def fetch_brands():
    resp = requests.get(BRANDS_URL, headers=HEADERS)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    print("✅ Loaded brand list page:", resp.url)

    elem_selector = "#pagecontent > table:nth-of-type(3) > tr:nth-of-type(1) > td:nth-of-type(1) > table"
    inner_table = soup.select_one(elem_selector)
    if not inner_table:
        raise RuntimeError("❌ Brand table not found on page.")

    brands = []
    for a in inner_table.find_all("a", href=True):
        href = a["href"]
        if href.startswith("../models/"):
            brand_name = a.get_text(strip=True)
            brand_url = urljoin(BRANDS_URL, href)
            brands.append((brand_name, brand_url))
    return brands


def crawl_brands():
    """Insert all brands into the database (skip if already exists)."""
    brands = fetch_brands()
    print(f"Fetched {len(brands)} brands")

    for name, href in brands:
        insert_new_brand(cnxn, name, href)
    print("✅ Database updated with brand list.")

# ============================================================
#                   MODEL CRAWLER
# ============================================================
def get_html(url: str):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")
    except requests.RequestException as e:
        print(f"❌ Failed to load {url}: {e}")
        return None


def extract_year_links(soup: BeautifulSoup) -> dict[str, str]:
    years_table = soup.select_one("#pagecontent > table.zebra")
    if not years_table:
        raise RuntimeError("❌ Couldn't find the years table.")
    year_urls = {}
    for a in years_table.select("a[href*='motorcycle-models']"):
        if match := re.search(r"(\d{4})-motorcycle-models", a["href"]):
            year_urls[match.group(1)] = urljoin(YEARS_URL, a["href"])
    return year_urls


def parse_model_table(year: str, url: str):
    soup = get_html(url)
    if not soup:
        print(f"⚠️ Skipping {year} — couldn't load page.")
        return

    table = soup.select_one("#pagecontent > table.zebra")
    if not table:
        print(f"⚠️ No models table for {year}")
        return

    for row in table.select("tr"):
        cells = row.select("td")
        if not cells:
            continue
        a = cells[0].find("a", href=True)
        if not a:
            continue

        model_name = a.get_text(strip=True)
        model_url = urljoin(url, a["href"])
        rating_link = cells[1].find("a", href=True) if len(cells) > 1 else None
        rating_url = urljoin(url, rating_link["href"]) if rating_link else None

        insert_new_model(cnxn, model_url, year, model_name, rating_url)


def crawl_models():
    soup = get_html(YEARS_URL)
    if not soup:
        raise SystemExit("❌ Could not load the years list page.")

    year_urls = extract_year_links(soup)
    if not year_urls:
        raise SystemExit("❌ No year URLs found.")

    for year, url in sorted(year_urls.items(), reverse=True):
        print(f"\n📅 Scraping models for year: {year}")
        parse_model_table(year, url)

    print("\n✅ Model crawling completed successfully.")





# ============================================================
#                   MAIN ENTRY POINT
# ============================================================
# if __name__ == "__main__":
#     if len(sys.argv) < 2:
#         print("Usage:")
#         print("  python crawler.py brands   → Crawl & update brands")
#         print("  python crawler.py models   → Crawl & update motorcycle models")
#         sys.exit(1)
#
#     mode = sys.argv[1].lower().strip()
#     print("🏍️ Starting Bikez model crawler...")
#
#     if mode == "brands":
#         crawl_brands()
#     elif mode == "models":
#         crawl_models()
#     else:
#         print(f"❌ Unknown mode '{mode}'. Use 'brands' or 'models'.")
