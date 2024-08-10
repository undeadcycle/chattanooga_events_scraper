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
execute_grid_search = True
execute_find_iframes = True
execute_check_shadow_dom =True
execute_find_potential_containers =True
execute_scroll_page = True
execute_save_html =True
execute_capture_network_requests = False
execute_save_events_to_csv = True

# 
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
        "details": {"div": {"class": "tribe-events-calendar-list__event-description tribe-common-b2 tribe-common-a11y-hidden"}},
        "recurrence": {"span": {"class": "tec_series_marker__title"}}, # PLACEHOLDER

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
    },

    "CHA Guide Things To Do": {
        "url": "https://www.cha.guide/explore/things-to-do-in-chattanooga-this-week",
        "content_list_class": {"div": {"class": "flex-table centered w-dyn-items"}},
        "item_attr": {"div": {"role": "listitem"}},
        "title": {"h3": {"class": "event-title"}},
        "date": {"div": {"class": "event-card-date"}},
        "month": {"div": {"class": "event-month"}},
        "time": {"div": {"class": "smaller-text bottom-margin---10px"}},
        "img": {
            "container": {"div": {"class": "event-image---horizontal"}},
            "parse_method": "style_background",
        },
        "location": {"div": {"class": "location-2"}},
        "recurrence": {"div": {"class": "smaller-text bottom-margin---5px"}},
        "category": {"div": {"class": "in-line smaller-text"}},
        "details": {"div": {"class": "truncate"}},
        "url_selector": {"a": {"class": "event-card horizontal-image w-inline-block"}},
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
    chromedriver_autoinstaller.install()
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome()
    
    try:
        driver.get(url)
        time.sleep(5)  # Wait for JavaScript to load content
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

def extract_shadow_content(driver, shadow_selectors, content_selector):
    shadow_root = find_shadow_element(driver, shadow_selectors)
    content_list = shadow_root.find_element(By.CSS_SELECTOR, content_selector)
    return content_list.get_attribute('innerHTML')

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

            if execute_capture_network_requests:
                capture_network_requests(site_name, driver)

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

        driver.quit()

if __name__ == "__main__":
    main()

####################
# BUGS & TODOS
####################


# TODO: category function

# TODO: details function

# BUG: rewrite date function to work on all sites (output times as AM/PM)

# TODO: add a time and price function (time could be included in date function)

# TODO: pull individual functions out of extract_events

# TODO: display image link as an image instead of a url

# BUG: fix event url and location in pulse

# TODO: consider adding capture network requests

# TODO: refactor debugging calls

# TODO: do need the chromedriver install statements? should i setup a new env and kernel for this script? containerize it?

# BUG: capture_network_requests breaks code

# BUG: need to allow recurrence = None (other dict attributes as well)

# BUG: script fails to establish connection when extracting shadow content on times free press

####################
# THINGS DONE
####################

###
# 8-6-24
###

# Started adding times free press
    # debugging: failed to find content list class
        # grid search function added
        # find iframes function added
        # check shadow dom function added (event list appears to be in shadow dom
        # find potential containers function added
        # scroll page function added
        # save html function added

# Consolidated debugging functions into a single section for readability and maintainability

###
# 8-8-24
###

# fixed broken webdriver call: driver = webdriver.chrome(service=service)
# added save_events_to_csv function
# added capture_network_requests function
# started refactoring debugging calls
    # added booleans
    # added some calls to main execution
    # modified main execution to save shadow dom content if save_html is called
    # moved logs and data to folders for easier access and to declutter the project root directory
# added dictionary entry for Chett Library