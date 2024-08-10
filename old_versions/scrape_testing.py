from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time

# Configuration for a single site (for example: "Visit Chattanooga")
SITE = {
    "name": "Choose Chatt",
    "url": "https://choosechatt.com/chattanooga-events/"
}

def fetch_page(url):
    options = Options()
    options.add_argument("--headless")  # Run in headless mode (no GUI)
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        driver.get(url)
        time.sleep(5)  # Wait for JavaScript to load content
        return driver.page_source
    except Exception as e:
        print(f"Error fetching the page: {e}")
        return None
    finally:
        driver.quit()

def parse_html(html_content):
    return BeautifulSoup(html_content, 'html.parser')

def log_parsed_html(parsed_content, site_name):
    with open(f"{site_name}_parsed_log.html", "w", encoding='utf-8') as file:
        file.write(str(parsed_content))

def main():
    site_name = SITE["name"]
    url = SITE["url"]
    
    print(f"Fetching and parsing {site_name}")
    html_content = fetch_page(url)  # This should be using Selenium
    if html_content:
        parsed_content = parse_html(html_content)
        print(f"Length of parsed content: {len(str(parsed_content))}")
        log_parsed_html(parsed_content, site_name)
        print(f"Parsed HTML content has been logged to {site_name}_parsed_log.html")
    else:
        print(f"Skipping {site_name} due to fetch error")

if __name__ == "__main__":
    main()
