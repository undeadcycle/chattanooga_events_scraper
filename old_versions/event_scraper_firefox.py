from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from datetime import datetime
from dateutil import parser
import time
import re
import logging


####################
# CONFIGURATION
####################

# Setup logging to a file
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='web_scraper.log',  # Specify the log file name
    filemode='w'  # 'w' to overwrite the log file each time, 'a' to append to it
)

SITES = {
    "Visit Chattanooga": {
        "url": "https://www.visitchattanooga.com/events/",
        "content_list_class": {"div": {"class": "content grid"}},
        "item_attr": {"div": {"data-type": "events"}},
        "title": {"a": {"class": "title truncate"}},
        "date": {"span": {"class": "mini-date-container"}}, # now broken since dateutil. Check for start and end times
        "img": { # Need to display as image
            "img": {"class": "thumb"},
            "parse_method": "lazy-src"
        },
        "location": {"li": {"class": "locations truncate"}},
        "recurrence": {"li": {"class": "recurrence"}},
    },

    "CHA Guide Events": {
        "url": "https://www.cha.guide/events",
        "content_list_class": {"div": {"class": "flex-table w-dyn-items"}},
        "item_attr": {"div": {"role": "listitem"}},
        "title": {"h3": {"class": "event-title"}},
        "date": {"div": {"class": "event-date-div"}}, # now broken since dateutil. Check for start and end times
        "img": {
            "parse_method": "none",
        },
        "location": {"div": {"class": "location-2"}},
        "recurrence": {"div": {"class": "event---category-circle"}},
        "category": {"div": {"class": "event---category-circle"}},
        "details": {"div": {"class": "smaller-text bottom-margin---5px"}},
    },
    
    "Chattanooga Pulse": {
        "url": "https://www.chattanoogapulse.com/search/event/the-pulse-event-search/#page=1", # no event url
        "content_list_class": {"div": {"id": "event_list_div"}},
        "item_attr": {"div": {"class": "event_result"}},
        "title": {"h4": {"class": "event_title"}},
        "date": {"p": {"class": "event_date"}}, # need to format as AM/PM
        "img": { # Need to display as image
            "container": {"div": {"class": "event_thumb"}},
            "tag": "img",
            "attr": "srcset",
            "parse_method": "srcset_220w"
        },
        "location": {"a": {}}, # outputs title instead of location
        "recurrence": {"p": {"class": "cats"}},
        "details": {"div": {"class": "smaller-text bottom-margin---5px"}},

    },
    
    "Times Free Press": {
        "url": "https://www.timesfreepress.com/tfpevents/?_evDiscoveryPath=/",
        "shadow": True,
        "shadow_selectors": ["shadow-host-selector", "nested-shadow-host-selector"],
        "content_selector": "content-list-selector",
        "title_selector": "h1.title",
        "url_selector": "a.link",
        "date_selector": "span.date",
        "start_time_selector": "span.start",
        "end_time_selector": "span.end",
        "location_selector": "div.location",
        "recurrence_selector": "span.recurrence",
        "image_selector": "img.thumbnail",
        "price_selector": "", 
    },
}

####################
# FETCHING & PARSING
####################

def fetch_page(url):
    service = Service(GeckoDriverManager().install())
    options = Options()
    # options.add_argument("-headless")  # Run in headless mode if needed
    
    driver = webdriver.Firefox(service=service, options=options)
    
    try:
        driver.get(url)
        time.sleep(5)  # Wait for JavaScript to load content
        scroll_page(driver)  # Scroll the page to ensure all content is loaded
        return driver.page_source, driver
    except Exception as e:
        logging.error(f"Error fetching the page: {e}")
        return None, driver


def parse_html(html_content):
    return BeautifulSoup(html_content, 'html.parser')

def find_shadow_element(driver, selectors):
    element = driver
    for selector in selectors:
        element = element.find_element(By.CSS_SELECTOR, selector)
        element = driver.execute_script("return arguments[0].shadowRoot", element)
    return element

####################
# DEBUGGING 
####################

def grid_search(html_content):
    grid_match = re.search(r'<div[^>]*class="[^"]*grid[^"]*"', html_content)
    if grid_match:
        start = max(0, grid_match.start() - 500)
        end = min(len(html_content), grid_match.end() + 1000)
        logging.info(f"Grid search result: {html_content[start:end]}")
    else:
        logging.info("Could not find 'grid' class in the HTML")

def find_iframes(html_content):
    iframes = html_content.find_all('iframe')
    for iframe in iframes:
        logging.info(f"Found iframe: {iframe.get('src', 'No src attribute')}")

def check_shadow_dom(driver):
    shadow_hosts = driver.execute_script("""
        return Array.from(document.querySelectorAll('*')).filter(el => el.shadowRoot);
    """)
    for host in shadow_hosts:
        logging.info(f"Found Shadow DOM host: {host.tag_name}, id: {host.get_attribute('id')}")

def find_potential_containers(parsed_content):
    potential_containers = parsed_content.find_all('div', class_=lambda x: x and any(keyword in x.lower() for keyword in ['list', 'container', 'wrapper', 'events']))
    for container in potential_containers:
        logging.info(f"Potential container found: {container.get('class')}")

def scroll_page(driver):
    total_height = driver.execute_script("return document.body.scrollHeight")
    for i in range(1, total_height, 100):
        driver.execute_script(f"window.scrollTo(0, {i});")
        time.sleep(0.1)

def save_html(html_content, site_name):
    with open(f'{site_name}.html', 'w', encoding='utf-8') as f:
        f.write(html_content)

####################
# EXTRACTION 
####################

def extract_shadow_content(driver, shadow_selectors, content_selector):
    shadow_root = find_shadow_element(driver, shadow_selectors)
    content_list = shadow_root.find_element(By.CSS_SELECTOR, content_selector)
    return content_list.get_attribute('innerHTML')

def extract_events(parsed_content, config):
    events = []
    for event_element in parsed_content.select(config.get("content_selector", "div.event")):
        event = {
            "title": event_element.select_one(config["title_selector"]).get_text(strip=True) if config.get("title_selector") else None,
            "url": event_element.select_one(config["url_selector"])["href"] if config.get("url_selector") else None,
            "date": event_element.select_one(config["date_selector"]).get_text(strip=True) if config.get("date_selector") else None,
            "start_time": event_element.select_one(config["start_time_selector"]).get_text(strip=True) if config.get("start_time_selector") else None,
            "end_time": event_element.select_one(config["end_time_selector"]).get_text(strip=True) if config.get("end_time_selector") else None,
            "location": event_element.select_one(config["location_selector"]).get_text(strip=True) if config.get("location_selector") else None,
            "recurrence": event_element.select_one(config["recurrence_selector"]).get_text(strip=True) if config.get("recurrence_selector") else None,
            "image_url": event_element.select_one(config["image_selector"])["src"] if config.get("image_selector") else None,
        }
        events.append(event)
    return events

def extract_image_url(img_config, item):
    if img_config['parse_method'] == 'lazy-src':
        img_tag, img_attrs = next(iter(img_config.items()))
        img_element = item.find(img_tag, **img_attrs)
        return img_element.get('data-lazy-src') or img_element.get('src') if img_element else None

    elif img_config['parse_method'] == 'srcset_220w':
        container_tag, container_attrs = next(iter(img_config['container'].items()))
        container = item.find(container_tag, **container_attrs)
        if not container:
            return None

        img_element = container.find(img_config['tag'])
        if not img_element or img_config['attr'] not in img_element.attrs:
            return None

        srcset = img_element[img_config['attr']]
        urls = srcset.split(', ')
        for url in urls:
            if '220w' in url:
                return url.split(' ')[0]
        return urls[0].split(' ')[0] if urls else None

    elif img_config['parse_method'] == 'none':
        return None
    
    return None

def parse_date_range(date_text):
    try:
        date_info = parser.parse(date_text, fuzzy=True)
        date = date_info.strftime("%Y-%m-%d")
        return {
            'date': date,
            'start_time': date_info.strftime("%H:%M") if date_info.hour else None,
            'end_time': None
        }
    except ValueError:
        logging.error(f"Couldn't parse date: {date_text}")
        return {
            'date': None,
            'start_time': None,
            'end_time': None
        }

def extract_events(parsed_content, config):
    events = []
    logging.info(f"Searching for content list with: {config['content_list_class']}")
    
    tag, class_name = next(iter(config['content_list_class'].items()))
    content_list = None
    
    if 'id' in class_name:
        content_list = parsed_content.find(tag, id=class_name['id'])
        logging.info(f"Attempting to find content list by id: {class_name['id']}")

    if not content_list and 'class' in class_name:
        content_list = parsed_content.find(tag, class_=class_name['class'])
        logging.info(f"Attempting to find content list by class: {class_name['class']}")

    if not content_list:
        content_list = parsed_content.find(tag)
        logging.info(f"Attempting to find content list by tag: {tag}")

    if not content_list:
        logging.error("Couldn't find content list")
        return events

    item_tag, item_attrs = next(iter(config['item_attr'].items()))
    items = content_list.find_all(item_tag, **item_attrs)

    for item in items:
        event = {}
        
        title_tag, title_attrs = next(iter(config['title'].items()))
        title_element = item.find(title_tag, **title_attrs)
        if title_element:
            event['title'] = title_element.text.strip()
            url_element = title_element if title_element.name == 'a' else title_element.find_parent('a')
            event['url'] = config["url"] + url_element['href'] if url_element else ''
        else:
            logging.error("Couldn't find title element")
            continue

        date_tag, date_attrs = next(iter(config['date'].items()))
        date_element = item.find(date_tag, **date_attrs)
        if date_element:
            date_text = date_element.text.strip()
            date_info = parse_date_range(date_text)
            event.update(date_info)
        else:
            event.update({
                'date': None,
                'start_time': None,
                'end_time': None
            })

        if config.get("img"):
            event['image_url'] = extract_image_url(config["img"], item)
        else:
            event['image_url'] = None

        location_tag, location_attrs = next(iter(config['location'].items()))
        location_element = item.find(location_tag, **location_attrs)
        event['location'] = location_element.text.strip() if location_element else None

        recurrence_tag, recurrence_attrs = next(iter(config['recurrence'].items()))
        recurrence_element = item.find(recurrence_tag, **recurrence_attrs)
        event['recurrence'] = recurrence_element.text.strip() if recurrence_element else None

        events.append(event)
    
    return events

####################
# EXECUTION
####################

def main():
    for site_name, config in SITES.items():
        url = config["url"]
        logging.info(f"Fetching and parsing {site_name}")

        result = fetch_page(url)
        if result:
            html_content, driver = result
            if html_content:
                save_html(html_content, site_name)  # Save HTML for debugging
                # Check if the site uses Shadow DOM
                if config.get("shadow"):
                    shadow_content = extract_shadow_content(driver, config["shadow_selectors"], config["content_selector"])
                    parsed_content = parse_html(shadow_content)
                else:
                    parsed_content = parse_html(html_content)

                events = extract_events(parsed_content, config)
                logging.info(f"Extracted {len(events)} events from {site_name}")
                for event in events:
                    logging.info(f"Title: {event.get('title')}")
                    logging.info(f"URL: {event.get('url')}")
                    logging.info(f"Date: {event.get('date')}")
                    logging.info(f"Location: {event.get('location')}")
                    logging.info(f"Recurrence: {event.get('recurrence')}")
                    logging.info(f"Image URL: {event.get('image_url')}")
                    logging.info("-" * 40)
            else:
                logging.error(f"Failed to fetch or parse the content from {site_name}")
            
            # Close the driver after we're done with it
            driver.quit()
        else:
            logging.error(f"Failed to initialize WebDriver for {site_name}")

            
if __name__ == "__main__":
    main()
