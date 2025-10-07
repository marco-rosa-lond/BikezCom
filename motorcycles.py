import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
from db.connection import execute_query



# Base URL listing motorcycle model years
YEARS_LIST_URL = "https://bikez.com/years/index.php"


def get_html(url):
    """Fetches and parses an HTML page into a BeautifulSoup object."""
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()  # raises an HTTPError if the request failed

    soup = BeautifulSoup(resp.text, "html.parser")
    print(f"✅ Loaded: {resp.url} | Title: {soup.title.string.strip() if soup.title else 'No title'}")
    return soup




def insert_motorcycle(motorcycle):
    year = motorcycle["year"]
    model = motorcycle["model_name"]
    model_url = motorcycle["model_url"]
    rating_url = motorcycle["rating_url"]

    sql = """
        IF NOT EXISTS (SELECT 1 FROM dbo.MotorcycleModels WHERE spec_url = ?)
        INSERT INTO dbo.MotorcycleModels (year, model_name, spec_url, rating_url) VALUES (?, ?, ?, ?)
        """

    execute_query(sql, (model_url, year, model, model_url, rating_url), commit=True)
    print("Inserted new motorcycle", model_url)



def navigate_motorcycle_models_by_year():
    """Navigates through motorcycle model years and extracts all model details."""

    # Step 1: Get the main years page
    soup = get_html(YEARS_LIST_URL)

    # Step 2: Locate the table containing year links
    years_table = soup.select_one("#pagecontent > table.zebra")
    if not years_table:
        raise Exception("❌ Couldn't find the years table on the page.")

    # Step 3: Extract all year URLs (e.g., '2024-motorcycle-models')
    year_urls = {}
    for a in years_table.find_all("a", href=True):
        match = re.search(r"(\d{4})-motorcycle-models", a["href"])
        if match:
            year = match.group(1)
            year_urls[year] = urljoin(YEARS_LIST_URL, a["href"])

    if not year_urls:
        raise Exception("❌ No year URLs were found.")

    # Step 4: Iterate through each year and scrape its models
    for year, url in year_urls.items():
        print(f"\n📅 Scraping models for year: {year}")
        model_soup = get_html(url)

        models_table = model_soup.select_one("#pagecontent > table.zebra")
        if not models_table:
            print(f"⚠️ No models table found for {year}. Skipping...")
            continue  # Skip this year instead of stopping the whole script

        # Step 5: Extract model info from table rows
        for row in models_table.find_all("tr"):
            cells = row.find_all("td")
            if not cells:
                continue  # Skip empty header rows or malformed rows

            motorcycle = {
                "year": year,
                "model_name": None,
                "model_url": None,
                "rating_url": None
            }

            # First column → Model name + model link
            a = cells[0].find("a", href=True)
            if a:
                motorcycle["model_name"] = a.get_text(strip=True)
                motorcycle["model_url"] = urljoin(url, a["href"])

            # Second column → Rating link (optional)
            rating_link = cells[1].find("a", href=True) if len(cells) > 1 else None
            if rating_link:
                motorcycle["rating_url"] = urljoin(url, rating_link["href"])

            insert_motorcycle(motorcycle)


# Run the scraper
if __name__ == "__main__":
    navigate_motorcycle_models_by_year()
