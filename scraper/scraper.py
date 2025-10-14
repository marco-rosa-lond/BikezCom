import random, time

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from db_helper import *
import threading
from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem
import re, json

# Define filters
software_names = [SoftwareName.CHROME.value]
operating_systems = [OperatingSystem.WINDOWS.value, OperatingSystem.LINUX.value]

# Initialize UserAgent with filters
user_agent_rotator = UserAgent(software_names=software_names, operating_systems=operating_systems, limit=100)


def clean_json_string(s):
    # Remove HTML tags if any
    s = re.sub(r'<[^>]+>', '', s)
    # Replace unescaped newlines inside strings
    s = s.replace('\n', ' ')
    # Remove multiple spaces
    s = re.sub(r'\s{2,}', ' ', s)
    # Strip any trailing commas before closing braces/brackets
    s = re.sub(r',(\s*[}\]])', r'\1', s)
    return s.strip()

def get_brand_from_script(soup):
    scripts = soup.find_all("script", type="application/ld+json")
    for s in scripts:
        content = s.string

        if not content:
            continue

        if '"@type":"Motorcycle"' in content or '"@type": "Motorcycle"' in content:
            try:
                json_data = clean_json_string(content)
                motorcycle_data = json.loads(json_data)
                brand = motorcycle_data.get("brand", {}).get("name")
                return brand
            except json.JSONDecodeError:
                print("Error decoding JSON, check if JSON IS MALFORMED")
    return ""



def scrape_model_page(page, url):
    page.goto(url, wait_until="networkidle")
    html = page.content()

    soup = BeautifulSoup(html, 'html.parser')
    b = get_brand_from_script(soup)

    th = page.query_selector("th #GENERAL")
    if not th:
        print("⚠️ GENERAL <th> not found")

    table = th.evaluate_handle("node => node.closest('table')")
    rows = table.query_selector_all("tr")
    specs = []

    section_desc = ""
    section_id = ""

    for row in rows:
        th_cell = row.query_selector("th")
        section_desc = th_cell.inner_text().strip() if th_cell is not None else section_desc
        div = th_cell.query_selector("div") if th_cell else None
        section_id = div.get_attribute("id") if div is not None else section_id

        tds = row.query_selector_all("td")
        if len(tds) == 2:
            label = tds[0].inner_text().strip()
            text = tds[1].inner_text().strip()
            specs.append({
                "brand": b,
                "section_id": section_id,
                "section_desc": section_desc,
                "label": label,
                "text": text
            })
    return specs, html


def worker(worker_id):
    ua = user_agent_rotator.get_random_user_agent()
    conn = get_connection()

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )

        context = browser.new_context(user_agent=ua)
        page = context.new_page()
        print(f"worker:{worker_id}  🏁 Started with UA: {ua[:40]}...")


        while True:
            time.sleep(random.uniform(0.5, 1.5))
            row = claim_next_model(conn)
            if not row:
                print(f"✅ No more pending models. Exiting.")
                break
            model_id, url = row
            print(f"[worker:{worker_id} - Scraping {url} (id={model_id})")
            try:
                specs, html = scrape_model_page(page, url)

                time.sleep(random.uniform(0.2, 1))
                insert_specs(conn, model_id, specs)
                insert_model_html(conn, model_id, html)
                mark_model_done(conn, model_id)
                print(f"✅ Saved {len(specs)} specs for id={model_id}")
            except Exception as e:
                print(f"❌ Error for id={model_id}: {e}")
                if "net::ERR_CONNECTION_REFUSED" in str(e) or 'networkidle' in str(e):
                    time.sleep(10)
                    print("waiting for network connection...")
                    pass
                else:
                    mark_model_failed(conn, model_id, e)

        browser.close()
        conn.close()



def run_scraper(num_workers=3):
    threads = []
    for i in range(num_workers):
        t = threading.Thread(target=worker, args=(i+1,))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    print("🎉 All workers finished!")


