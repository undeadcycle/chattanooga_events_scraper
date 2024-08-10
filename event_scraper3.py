from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import chromedriver_autoinstaller
from bs4 import BeautifulSoup
from datetime import datetime
from dateutil import parser
import time
import re
import logging
import csv
import os

####################
# CONFIGURATION
####################

# Setup logging to a file

LOG_FOLDER = 'logs'
DATA_FOLDER = 'data'

if not os.path.exists(LOG_FOLDER):
    os.makedirs(LOG_FOLDER)

if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

logging.basicConfig(
    level = logging.INFO, 
    format = '%(asctime)s - %(levelname)s - %(message)s',
    filename = os.path.join(LOG_FOLDER, 'web_scraper.log'),  
    filemode = 'w'  # 'w' to overwrite the log file each time, 'a' to append to it
)

# DEBUGGING BOOLEANS
execute_debugging = False

execute_scroll_page = True
execute_save_html =True
execute_save_events_to_csv = True

# 
SITES = {
 
    "Visit Chattanooga": {
        "url": "https://www.visitchattanooga.com/events/",
        "content_list_class": {"div": {"class": "content grid"}},
        "item_attr": {"div": {"data-type": "events"}},
        "title": {"a": {"class": "title truncate"}},
        "date": {"span": {"class": "mini-date-container"}}, 
        "time": {},
        "img": { 
            "img": {"class": "thumb"},
            "parse_method": "lazy-src"
        },
        "location": {"li": {"class": "locations truncate"}},
        "recurrence": {"li": {"class": "recurrence"}},
        "category": {},
        "details": {},
        "price": {},
    },

    "CHA Guide Events": {
        "url": "https://www.cha.guide/events",
        "content_list_class": {"div": {"class": "flex-table w-dyn-items"}},
        "item_attr": {"div": {"role": "listitem"}},
        "title": {"h3": {"class": "event-title"}},
        "date": {"div": {"class": "event-date-div"}}, 
        "time": {},
        "img": {
            "parse_method": "none",
        },
        "location": {"div": {"class": "location-2"}},
        "recurrence": {"div": {"class": "event---category-circle"}},
        "category": {"div": {"class": "event---category-circle"}},
        "details": {"div": {"class": "smaller-text bottom-margin---5px"}},
        "price": {},
    },
    
    "Chattanooga Pulse": {
        "url": "https://www.chattanoogapulse.com/search/event/the-pulse-event-search/#page=1", 
        "content_list_class": {"div": {"id": "event_list_div"}},
        "item_attr": {"div": {"class": "event_result"}},
        "title": {"h4": {"class": "event_title"}},
        "date": {"p": {"class": "event_date"}}, 
        "time": {},
        "img": { 
            "container": {"div": {"class": "event_thumb"}},
            "tag": "img",
            "attr": "srcset",
            "parse_method": "srcset_220w"
        },
        "location": {"a": {}}, # PLACEHOLDER
        "recurrence": {"p": {"class": "cats"}},
        "category": {},
        "details": {"div": {"class": "smaller-text bottom-margin---5px"}},
        "price": {},

    },

    'Chatt Library': {
        'url': 'https://chattlibrary.org/events/',
        "content_list_class": {"div": {"class": "tribe-events-calendar-list"}},
        "item_attr": {"div": {"class": "tribe-common-g-row tribe-events-calendar-list__event-row"}},

        "title": {"a": {"class": "tribe-events-calendar-list__event-title-link tribe-common-anchor-thin"}},
        "date": {"time": {"class": "tribe-events-calendar-list__event-date-tag-datetime', 'attribute': 'datetime"}}, 
        "time": {"time": {"class": "tribe-events-calendar-list__event-datetime', 'attribute': 'datetime"}},
        "img": {
            "parse_method": "none",
            "container": {"div": {"class": "tribe-events-calendar-list__event-featured-image-wrapper tribe-common-g-col"}},
            "tag": "img",
            "attr": "src",
            "???": {"class": "tribe-events-calendar-list__event-featured-image-link"},
        },
        "location": {"span": {"class": "tribe-events-calendar-list__event-venue-title tribe-common-b2--bold"}},
        "recurrence": {"span": {"class": "tec_series_marker__title"}}, # PLACEHOLDER
        "category": {},
        "details": {"div": {"class": "tribe-events-calendar-list__event-description tribe-common-b2 tribe-common-a11y-hidden"}},
        "price": {},

    },
    
    "Chattanooga Chamber": {
        "url": "https://web.chattanoogachamber.com/events/",
        "content_list_class": {"div": {"class": "fc-content-skeleton"}},
        "item_attr": {"a": {"class": "fc-day-grid-event"}},
        "title": {"span": {"class": "fc-title"}},
        "date": {"td": {"class": "fc-day-top", "data-date": True}},
        "time": {"span": {"class": "fc-time"}},
        "img": {
            "parse_method": "none",
        },
        "location": {"div": {"class": "fc-content"}},  # Note: Location might not be directly available
        "recurrence": {"div": {"class": "fc-content"}},  # Note: Recurrence info might not be directly available
        "category": {"a": {"class": True}},  # The class of the event link contains category info
        "details": {},
        "price": {},
    },

    "CHA Guide Things To Do": {
        "url": "https://www.cha.guide/explore/things-to-do-in-chattanooga-this-week",
        "content_list_class": {"div": {"class": "flex-table centered w-dyn-items"}},
        "item_attr": {"div": {"role": "listitem"}},
        "title": {"h3": {"class": "event-title"}},
        "date": {"div": {"class": "event-card-date"}},
        "time": {"div": {"class": "smaller-text bottom-margin---10px"}},
        "img": {
            "container": {"div": {"class": "event-image---horizontal"}},
            "parse_method": "style_background",
        },
        "location": {"div": {"class": "location-2"}},
        "recurrence": {},
        "category": {"div": {"class": "in-line smaller-text"}},
        "details": {"div": {"class": "truncate"}},
        "price": {},
    },

    "Nooga Today": {
        "url": "https://noogatoday.6amcity.com/events#/",
        "content_list_class": {"div": {"class": ""}},
        "item_attr": {"div": {"class": "csEvWrap csEventTile csEvFindMe"}},
        "title": {"span": {"class": ""}},
        "date": {"div": {"class": "csStaticSize"}, "contains": "svg"},
        "img": {
            "container": {"div": {"class": "csimg csImg"}},
            "parse_method": "style_background",
        },
        "location": {"span": {"class": ""}, "parent": {"class": "cityVenue"}}, #split across multiple spans
        "recurrence": {"div": {"class": "csIconRow"}},
        "category": {"div": {"class": "csBadgeBar"}},
        "details": {"div": {"class": "csIconInfo"}},
        "url_selector": {"a": {"href": True}},
    },

    # "Times Free Press": {
    #     "url": "https://www.timesfreepress.com/tfpevents/?_evDiscoveryPath=/",
    #     "shadow": True,
    #     "shadow_selectors": ["shadow-host-selector", "nested-shadow-host-selector"],
    #     "content_selector": "content-list-selector",
    #     "title_selector": "h1.title",
    #     "url_selector": "a.link",
    #     "date_selector": "span.date",
    #     "start_time_selector": "span.start",
    #     "end_time_selector": "span.end",
    #     "image_selector": "img.thumbnail",
    #     "location_selector": "div.location",
    #     "recurrence_selector": "span.recurrence",
    #     "category_selector": "",
    #     "details_selector": "",
    #     "price_selector": "", 
    # },

}

####################
# FETCHING & PARSING
####################

def fetch_page(url):
    chromedriver_autoinstaller.install()
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome()
    
    try:
        driver.get(url)
        time.sleep(5)  # Wait for JavaScript to load content
        if execute_scroll_page:
            scroll_page(driver)  # Scroll the page to ensure all content is loaded
        html_content = driver.page_source
        return html_content, driver
    except Exception as e:
        logging.error(f"Error fetching the page: {e}")
        return None, driver
    finally:
        driver.quit()


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
    file_name = os.path.join(LOG_FOLDER, f"{site_name}.html")
    with open(file_name, 'w', encoding='utf-8') as f:
        f.write(html_content)

def capture_network_requests(site_name, driver):
    network_file = os.path.join(DATA_FOLDER, f"{site_name}_network_request.txt")
    network_logs = []
    logs = driver.get_log('performance')
    for entry in logs:
        try:
            network_log = json.loads(entry['message'])['message']
            if network_log['method'] in ['Network.response', 'Network.request', 'Network.webSocket']:
                network_logs.append(network_log)
        except json.JSONDecodeError:
            print(f"Error parsing log: {entry['message']}")
    with open(network_file, 'a', encoding='utf-8') as f:
        for log in network_logs:
            f.write(json.dumps(log) + '\n')

def save_events_to_csv(events, site_name):
    file_name = os.path.join(DATA_FOLDER, f"{site_name}_events.csv")
    with open(file_name, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = events[0].keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for event in events:
            writer.writerow(event)

####################
# EXTRACTION 
####################

def extract_title_and_url(item, config):
    title_tag, title_attrs = next(iter(config.get('title', {}).items()), (None, None))
    if not title_tag:
        return "N/A", "N/A"
    
    title_element = item.find(title_tag, **title_attrs) if title_attrs else item.find(title_tag)
    if not title_element:
        return "N/A", "N/A"
    
    title = title_element.text.strip()
    url = config.get("url", "") + title_element.get('href', '') if title_element.name == 'a' else "N/A"
    return title, url

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

def extract_date_and_time(item, config):
    date_tag, date_attrs = next(iter(config.get('date', {}).items()), (None, None))
    if not date_tag:
        return "N/A", "N/A", "N/A"
    
    date_element = item.find(date_tag, **date_attrs) if date_attrs else item.find(date_tag)
    if not date_element:
        return "N/A", "N/A", "N/A"
    
    date_text = date_element.text.strip()
    date_info = parse_date_range(date_text)
    return date_info.get('date', "N/A"), date_info.get('start_time', "N/A"), date_info.get('end_time', "N/A")


def extract_image_url_lazy_src(item, config):
    img_config = config.get('img', {})
    if not img_config or img_config.get('parse_method') != 'lazy-src':
        return "N/A"
    
    img_tag, img_attrs = next(iter(img_config.items()))
    img_element = item.find(img_tag, **img_attrs)
    return img_element.get('data-lazy-src') or img_element.get('src') if img_element else "N/A"

def extract_image_url_srcset_220w(item, config):
    img_config = config.get('img', {})
    if not img_config or img_config.get('parse_method') != 'srcset_220w':
        return "N/A"
    
    container_tag, container_attrs = next(iter(img_config['container'].items()))
    container = item.find(container_tag, **container_attrs)
    if not container:
        return "N/A"

    img_element = container.find(img_config['tag'])
    if not img_element or img_config['attr'] not in img_element.attrs:
        return "N/A"

    srcset = img_element[img_config['attr']]
    urls = srcset.split(', ')
    for url in urls:
        if '220w' in url:
            return url.split(' ')[0]
    return urls[0].split(' ')[0] if urls else "N/A"

def extract_image_url_style_background(item, config):
    img_config = config.get('img', {})
    if not img_config or img_config.get('parse_method') != 'style_background':
        return "N/A"
    
    container_tag, container_attrs = next(iter(img_config['container'].items()))
    container = item.find(container_tag, **container_attrs)
    if not container or 'style' not in container.attrs:
        return "N/A"
    
    style = container['style']
    match = re.search(r'background-image:url\("(.+?)"\)', style)
    return match.group(1) if match else "N/A"

def extract_location(item, config):
    location_tag, location_attrs = next(iter(config.get('location', {}).items()), (None, None))
    if not location_tag:
        return "N/A"
    
    location_element = item.find(location_tag, **location_attrs) if location_attrs else item.find(location_tag)
    return location_element.text.strip() if location_element else "N/A"

def extract_recurrence(item, config):
    recurrence_tag, recurrence_attrs = next(iter(config.get('recurrence', {}).items()), (None, None))
    if not recurrence_tag:
        return "N/A"
    
    recurrence_element = item.find(recurrence_tag, **recurrence_attrs) if recurrence_attrs else item.find(recurrence_tag)
    return recurrence_element.text.strip() if recurrence_element else "N/A"

def extract_category(item, config, return_all=False):
    category_tag, category_attrs = next(iter(config.get('category', {}).items()), (None, None))
    if not category_tag:
        return "N/A"
    
    if return_all:
        category_elements = item.find_all(category_tag, **category_attrs) if category_attrs else item.find_all(category_tag)
        return [cat.text.strip() for cat in category_elements] if category_elements else ["N/A"]
    else:
        category_element = item.find(category_tag, **category_attrs) if category_attrs else item.find(category_tag)
        return category_element.text.strip() if category_element else "N/A"

def extract_details(item, config):
    details_tag, details_attrs = next(iter(config.get('details', {}).items()), (None, None))
    if not details_tag:
        return "N/A"
    
    details_element = item.find(details_tag, **details_attrs) if details_attrs else item.find(details_tag)
    return details_element.text.strip() if details_element else "N/A"

def extract_events(parsed_content, config):
    events = []
    content_list_tag, content_list_attrs = next(iter(config['content_list_class'].items()))
    content_list = parsed_content.find(content_list_tag, **content_list_attrs)
    
    if not content_list:
        logging.error("Couldn't find content list")
        return events

    item_tag, item_attrs = next(iter(config['item_attr'].items()))
    items = content_list.find_all(item_tag, **item_attrs)

    for item in items:
        event = {}
        event['title'], event['url'] = extract_title_and_url(item, config)
        event['date'], event['start_time'], event['end_time'] = extract_date_and_time(item, config)
        event['image_url'] = extract_image_url_lazy_src(item, config) or extract_image_url_srcset_220w(item, config) or extract_image_url_style_background(item, config)
        event['location'] = extract_location(item, config)
        event['recurrence'] = extract_recurrence(item, config)
        event['category'] = extract_category(item, config, return_all=True)
        event['details'] = extract_details(item, config)
        events.append(event)

        # Check if any of the event values are None
        if any(value is None for value in event.values()):
            continue
    
    return events

def extract_shadow_content(driver, shadow_selectors, content_selector):
    shadow_root = find_shadow_element(driver, shadow_selectors)
    content_list = shadow_root.find_element(By.CSS_SELECTOR, content_selector)
    return content_list.get_attribute('innerHTML')

def extract_shadow_events(parsed_content, config):
    shadow_events = []
    for shadow_element in parsed_content.select(config.get("content_selector", "div.event")):
        shadow_event = {
            "title": shadow_element.select_one(config["title_selector"]).get_text(strip=True) if config.get("title_selector") else None,
            "url": shadow_element.select_one(config["url_selector"])["href"] if config.get("url_selector") else None,
            "date": shadow_element.select_one(config["date_selector"]).get_text(strip=True) if config.get("date_selector") else None,
            "start_time": shadow_element.select_one(config["start_time_selector"]).get_text(strip=True) if config.get("start_time_selector") else None,
            "end_time": shadow_element.select_one(config["end_time_selector"]).get_text(strip=True) if config.get("end_time_selector") else None,
            "location": shadow_element.select_one(config["location_selector"]).get_text(strip=True) if config.get("location_selector") else None,
            "recurrence": shadow_element.select_one(config["recurrence_selector"]).get_text(strip=True) if config.get("recurrence_selector") else None,
            "image_url": shadow_element.select_one(config["image_selector"])["src"] if config.get("image_selector") else None,
        }
        shadow_events.append(shadow_event)
    return shadow_events

####################
# EXECUTION
####################

def main():
    for site_name, config in SITES.items():
        url = config["url"]
        logging.info(f"Fetching and parsing {site_name}")
        html_content, driver = fetch_page(url)
        if html_content:
            if execute_debugging:
                grid_search(html_content)
                find_iframes(html_content)
                check_shadow_dom(driver)
                find_potential_containers(parsed_content)
                capture_network_requests(site_name, driver)
                save_html(html_content, site_name)
            # Check if the site uses Shadow DOM
            if config.get("shadow"):
                shadow_content = extract_shadow_content(driver, config["shadow_selectors"], config["content_selector"])
                parsed_content = parse_html(shadow_content)
                if execute_save_html:
                    save_html(shadow_content, site_name)
            else:
                parsed_content = parse_html(html_content)
                if execute_save_html:
                    save_html(html_content, site_name)

            events = extract_events(parsed_content, config)
            if execute_save_events_to_csv:
                save_events_to_csv(events, site_name)
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


if __name__ == "__main__":
    main()

####################
# BUGS & TODOS
####################


# BUG: rewrite date function to work on all sites (output times as AM/PM)

# TODO: add a price function 

# TODO: separate time and date function

# TODO: display image link as an image instead of a url

# TODO: fix capture network requests

# TODO: refactor debugging calls

# TODO: do i need the chromedriver install statements? should i setup a new env and kernel for this script? containerize it?

# BUG: script fails to establish connection (red herring?) when extracting shadow content on times free press

# TODO: get past lightbox (choose chatt, nooga today [no longer uses lightbox?])

# TODO: create single csv for all sites together

# BUG: WARNING - Retrying (Retry(total=2, connect=None, read=None, redirect=None, status=None)) after connection broken by 'NewConnectionError('<urllib3.connection.HTTPConnection object at 0x7270816a7150>: Failed to establish a new connection: [Errno 111] Connection refused')': /session/8831fc9bba6122c89f4eb4f6d4502a9f
    # seems related to how the driver closes? all info seems to be pulled and the error happens durring transition to next site?

####################
# THINGS DONE
####################

'''
# 8-6-24

- Started adding times free press
- debugging: failed to find content list class
    - grid search function added
    - find iframes function added
    - check shadow dom function added (event list appears to be in shadow dom
    - find potential containers function added
    - scroll page function added
    - save html function added
- Consolidated debugging functions into a single section for readability and maintainability
---

# 8-8-24

- fixed broken webdriver call: driver = webdriver.chrome(service=service)
- added save_events_to_csv function
- added capture_network_requests function
- started refactoring debugging calls
    - added booleans
    - added some calls to main execution
    - modified main execution to save shadow dom content if save_html is called
    - moved logs and data to folders for easier access and to declutter the project root directory
- added dictionary entry for Chett Library
---

# 8-9-24

- added dictionary entry for chatt chamber
- added dictionary entry fo cha guides
- separated out functions for each selector in dictionary entries
- reorganized dictionary entries to have consistant selectors
- search for bugs: 
    - found: network connection broken by 'NewConnectionError'
- refactored debugging calls (may still need more, may be fine as is)
'''