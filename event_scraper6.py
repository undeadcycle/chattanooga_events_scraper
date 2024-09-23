from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import chromedriver_autoinstaller
from bs4 import BeautifulSoup
from datetime import datetime
from dateutil import parser
import pandas as pd
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
    filename = os.path.join(LOG_FOLDER, 'date_extraction.log'),  
    filemode = 'w'  # 'w' to overwrite the log file each time, 'a' to append to it
)

# DEBUGGING BOOLEANS
execute_debugging = True
execute_scroll_page = True
execute_save_html =True
execute_save_events_to_csv = False





# 
SITES = {
 
    "Visit Chattanooga": {
        "url": "https://www.visitchattanooga.com/events/",
        "content_list_class": {"div": {"class": "content grid"}},
        "item_attr": {"div": {"data-type": "events"}},
        "title": {"a": {"class": "title truncate"}},
        "event_url": {
            "parse_method": "title",
            "base_url": "https://www.visitchattanooga.com",
            "tag": "h4",
            "attrs": {"role": "heading"}, "a": {"href": True}
            },
        
        "date": {
            "extract_method": "attrs",
            "parse_method": "parser.parse",
            "tag": "span",
            "attrs": {"class": "mini-date-container"}
            }, 
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
        "event_url": {
            "parse_method": "tag",
            "base_url": "https://www.cha.guide",
            "tag": "a", 
            "attrs": {"href": True}
        },
        "date": {
            "extract_method": "attrs",
            "parse_method": "time_range",
            "tag": "div",
            # "attrs": {"class": "event-date-div"}
            "attrs": {"class": "smaller-text bottom-margin---10px"}
            }, 
        
        "time": {"div": {"class": "in-line right-margin---5px"}}, # endswith"</div> ??
        "img": {
            "container": {"div": {"class": "event-image---horizontal"}},
            "parse_method": "style_background",
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
        "event_url": {
            "parse_method": "title",
            "base_url": "",
            },
        "date": {
            "extract_method": "tag",
            "parse_method": "split",
            "tag": {"p":{"class": "event-date"}}
            }, 
        
        "time": {"p": {"class": "event_date"}},
        "img": { 
            "container": {"div": {"class": "event_thumb"}},
            "tag": "img",
            "attr": "srcset",
            "parse_method": "srcset_220w"
        },
        "location": {"a": {"href": lambda x: x.startswith("https://www.chattanoogapulse.com/locations/")}},
        "recurrence": {},
        "category": {"p": {"class": "cats"}},
        "details": {"p": {"class": "description"}},
        "price": {},

    },

    'Chatt Library': {
        'url': 'https://chattlibrary.org/events/',
        "content_list_class": {"div": {"class": "tribe-events-calendar-list"}},
        "item_attr": {"div": {"class": "tribe-common-g-row tribe-events-calendar-list__event-row"}},
        "title": {"a": {"class": "tribe-events-calendar-list__event-title-link tribe-common-anchor-thin"}},
        "event_url": {
            "parse_method": "title",
            "base_url": ""
            },
        "date": {
            "extract_method": "attrs",
            "parse_method": "split '@'",
            "tag": {"span": {"class": "tribe-event-date-start"}},
            "attrs": {"class": "tribe-event-date-start"}
            # "tag": {"time": {"class": "tribe-events-calendar-list__event-date-tag-datetime', 'attribute': 'datetime"}}
            }, 
        
        "time": {"span": {"class": "tribe-event-date-start"}}, # end time: span class="tribe-event-time"
        "img": {
            "parse_method": "none",
            "container": {"div": {"class": "tribe-events-calendar-list__event-featured-image-wrapper tribe-common-g-col"}},
            "tag": "img",
            "attr": "src",
            "???": {"class": "tribe-events-calendar-list__event-featured-image-link"},
        },
        "location": {"span": {"class": "tribe-events-calendar-list__event-venue-title tribe-common-b2--bold"}},
        "recurrence": {}, 
        "category": {},
        "details": {"div": {"class": "tribe-events-calendar-list__event-description tribe-common-b2 tribe-common-a11y-hidden"}},
        "price": {},

    },
    

####################################################################################################################

    # "CHA Guide Things To Do": {
    #     "url": "https://www.cha.guide/explore/things-to-do-in-chattanooga-this-week",
    #     "content_list_class": {"div": {"class": "flex-table centered w-dyn-items"}},
    #     "item_attr": {"div": {"role": "listitem"}},
    #     "title": {"h3": {"class": "event-title"}},
    #     "event_url": {
    #         "parse_method": "tag",
    #         "base_url": "https://www.cha.guide",
    #         "tag": "a", 
    #         "attrs": {"class": "event-card horizontal-image w-inline-block", "href": True}
    #     },

    #     "date": {
    #         "extract_method": "attrs",
    #         "parse_method": "parser.parse",
    #         "tag": "div",
    #         "attrs": {"class": "event-date-div"}
    #         }, 
    #     "time": {"div": {"class": "in-line right-margin---5px"}}, # endswith"</div> ??
    #     "img": {
    #         "container": {"div": {"class": "event-image---horizontal"}},
    #         "parse_method": "style_background",
    #     },
    #     "location": {"div": {"class": "location-2"}},
    #     "recurrence": {},
    #     "category": {"div": {"class": "in-line smaller-text"}},
    #     "details": {"div": {"class": "truncate"}},
    #     "price": {},
    # },

    # "Chattanooga Chamber": {
    #     "url": "https://web.chattanoogachamber.com/events/",
    #     "content_list_class": {"div": {"class": "fc-month-view"}},
    #     "item_attr": {"a": {"class": "fc-day-grid-event"}},
    #     "title": {"span": {"class": "fc-title"}},
    #     "event_url": {
    #         "parse_method": "tag",
    #         "base_url": "https://web.chattanoogachamber.com",
    #         "tag": "a", 
    #         "attrs": {"a": {"class": "fc-day-grid-event", "href": True}}
    #     },
    #     "date": {
    #         "extract_method": "attrs",
    #         "parse_method": "parser.parse",
    #         "tag": "td",
    #         "attrs": {"class": "fc-day-top"}
    #         }, 
        
    #     "time": {"span": {"class": "fc-time"}},
    #     "img": {
    #         "parse_method": "none",
    #     },
    #     "location": {"div": {"class": "fc-content"}},  # Note: Location might not be directly available
    #     "recurrence": {"div": {"class": "fc-content"}},  # Note: Recurrence info might not be directly available
    #     "category": {"a": {"class": True}},  # The class of the event link contains category info
    #     "details": {},
    #     "price": {},
    # },

####################################################################################################################

    # "Nooga Today": {
    #     "url": "https://noogatoday.6amcity.com/events#/",
    #     "content_list_class": {"div": {"class": ""}},
    #     "item_attr": {"div": {"class": "csEvWrap csEventTile csEvFindMe"}},
    #     "title": {"span": {"class": ""}},
    #     "event_url": {},
    #     "date": {"div": {"class": "csStaticSize"}, "contains": "svg"},
    #     "img": {
    #         "container": {"div": {"class": "csimg csImg"}},
    #         "parse_method": "style_background",
    #     },
    #     "location": {"span": {"class": ""}, "parent": {"class": "cityVenue"}}, #split across multiple spans
    #     "recurrence": {"div": {"class": "csIconRow"}},
    #     "category": {"div": {"class": "csBadgeBar"}},
    #     "details": {"div": {"class": "csIconInfo"}},
    #     "url_selector": {"a": {"href": True}},
    # },

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
        logging.info(f"{url} fetched")
        driver.quit()



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
    soup = BeautifulSoup(html_content, 'html.parser')
    iframes = soup.find_all('iframe')
    if iframes:
        for iframe in iframes:
            logging.info(f"Found iframe: {iframe.get('src', 'No src attribute')}")
    else:
        logging.info("No iframes found in HTML")


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

def save_parsed(parsed_content, site_name):
    file_name = os.path.join(LOG_FOLDER, f"{site_name}_parsed.html")
    with open(file_name, 'w', encoding='utf-8') as f:
        f.write(parsed_content.prettify())

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

def parse_html(html_content):
    logging.info("#### HTML PARSED ####")
    logging.info("#" * 80)
    return BeautifulSoup(html_content, 'html.parser')

def extract_title(item, config):
    title_tag, title_attrs = next(iter(config.get('title', {}).items()), (None, None))
    logging.info(f"title_tag: {title_tag}")
    logging.info(f"title_attrs: {title_attrs}")
    if not title_tag:
        return "N/A"
    
    title_element = item.find(title_tag, **title_attrs)
    logging.info(f"title_element: {title_element}")
    if not title_element:
        return "N/A"
    
    a_tag = title_element.find('a') if title_element.name != 'a' else title_element
    title = a_tag.text.strip() if a_tag else title_element.text.strip()
    
    return title, title_element

def extract_event_url(item, title_element, config):

    url_config = config.get('event_url', {})
    logging.info(f"url_config: {url_config}")
 
    base_url = url_config.get('base_url', '')  
    logging.info(f"base_url: {base_url}")  
    
    parse_method = url_config.get('parse_method')

    if parse_method == "title":

        href_element = title_element.get('href', '')
        logging.info(f"href_element: {href_element}")

        if href_element:
            url = base_url + href_element 
            logging.info(f"url: {url}")
            logging.info("*" * 80)
            return url
        else:
            a_tag = title_element.find('a')
            logging.info(f"a_tag: {a_tag}")
            href_element = a_tag.get('href', '') if a_tag else ''
            logging.info(f"href_element: {href_element}")
            url = base_url + href_element 
            logging.info(f"url: {url}")
            logging.info("*" * 80)
            return url


    if parse_method == "tag":

        url_tag = url_config.get('tag')
        logging.info(f"url_tag: {url_tag}")

        url_attrs = url_config.get('attrs', {})
        logging.info(f"url_attrs: {url_attrs}")
       
        # url_element = item.find(url_tag)
        # logging.info(f"url_element: {url_element}")

        url_element = item.find(url_tag, **url_attrs)
        logging.info(f"url_element: {url_element}")
        if not url_element or 'href' not in url_element.attrs:
            logging.info("*" * 80)
            return "N/A"

        url = url_element['href']
        logging.info(f"url: {url}")

        url = base_url + url if url != "N/A" and not url.startswith(('http://', 'https://')) else url
        logging.info(f"url: {url}")
        logging.info("*" * 80)

        return url

def parse_date_range(date_text, config):
    date_config = config.get('date', {})
    parse_method = date_config.get('parse_method')
    
    if parse_method == "parser.parse":
        date_info = parser.parse(date_text, fuzzy=True)
        logging.info(f"date_info: {date_info}")
        date = date_info.strftime("%m-%d")
        logging.info(f"date: {date}")
        time = date_info.strftime("%I:%M %p")
        logging.info(f"time: {time}")
        logging.info("*" * 80)
        return date, time

    if parse_method == "time_range":
        try:
            date_info = parser.parse(date_text, fuzzy=True)
            logging.info(f"date_info: {date_info}")
            date = date_info.strftime("%m-%d")
            logging.info(f"date: {date}")
            time = date_info.strftime("%I:%M %p")
            logging.info(f"time: {time}")
            logging.info("*" * 80)
            return date, time
        except:
            date_part, time_part = date_text.split("@")
            logging.info(f"date_part: {date_part}")
            logging.info(f"time_part: {time_part}")
            date_obj = parser.parse(date_part, fuzzy=True)
            logging.info(f"date_obj: {date_obj}")
            date = date_obj.strftime("%m-%d")
            logging.info(f"date: {date}")
            time = time_part
            logging.info(f"time: {time}")
            logging.info("*" * 80)
            return date, time


    if parse_method == "split":
        date_info, time_info = date_text.split(",")
        logging.info(f"date_info: {date_info}")
        logging.info(f"time_info: {time_info}")
        date_obj = datetime.strptime(date_info, "%b %d")
        logging.info(f"date_obj: {date_obj}")
        date = datetime.strftime(date_obj, "%m-%d")
        logging.info(f"date: {date}")
        time_info = time_info[6:14]
        logging.info(f"time_info: {time_info}")
        if time_info != "":
            time_obj = parser.parse(time_info)
            logging.info(f"time_obj: {time_obj}")
            time = datetime.strftime(time_obj, "%I:%M %p")
        else:
            time = "12:00 AM"
        logging.info(f"time: {time}")
        logging.info("*" * 80)
        return date, time
    if parse_method == "split '@'":
        date_info, time_info = date_text.split(" @ ")
        logging.info(f"date_info: {date_info}")
        logging.info(f"time_info: {time_info}")
        date_obj = datetime.strptime(date_info, "%B %d")
        logging.info(f"date_obj: {date_obj}")
        date = datetime.strftime(date_obj, "%m-%d")
        logging.info(f"date: {date}")
        
        time_obj = parser.parse(time_info)
        logging.info(f"time_obj: {time_obj}")
        time = datetime.strftime(time_obj, "%I:%M %p")
        logging.info(f"time: {time}")
        logging.info("*" * 80)
        return date, time


def extract_date_and_time(item, config):
    date_config = config.get('date', {})
    logging.info(f"date_config: {date_config}")
    extract_method = date_config.get('extract_method')
    logging.info(f"extract_method: {extract_method}")
    date_tag = date_config.get('tag')
    logging.info(f"date_tag: {date_tag}")
    date_attrs = date_config.get('attrs')
    logging.info(f"date_attrs: {date_attrs}")
    
    if not date_tag:
        logging.info("*" * 80)
        return "N/A", "N/A"
    
    if extract_method == "attrs":

        date_element = item.find(date_tag, **date_attrs) if date_attrs else item.find(date_tag)
        logging.info(f"date_element: {date_element}")


        
        if not date_element:
            logging.info("*" * 80)
            return "N/A", "N/A"
        
        date_text = date_element.text.strip()
        logging.info(f"date_text: {date_text}")
        

    elif extract_method == "tag":
        date_element = item.find(date_tag,)
        logging.info(f"date_element: {date_element}")
        date_text =date_element.text.strip()
        logging.info(f"date_text: {date_text}")

    

    date, time = parse_date_range(date_text, config)  
    if time == "12:00 AM":
        time = "Open link for time"
    logging.info("*" * 80)
    return date, time  

def extract_image_url(item, config):
    img_config = config.get('img', {})
    if not img_config:
        return "N/A"
    
    parse_method = img_config.get('parse_method')
    
    if parse_method == 'lazy-src':
        img_tag, img_attrs = next(iter(img_config.items()))
        img_element = item.find(img_tag, **img_attrs)
        return img_element.get('data-lazy-src') or img_element.get('src') if img_element else "N/A"
    
    elif parse_method == 'srcset_220w':
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
    
    elif parse_method == 'style_background':
        container_tag, container_attrs = next(iter(img_config['container'].items()))
        container = item.find(container_tag, **container_attrs)
        if not container or 'style' not in container.attrs:
            return "N/A"
        style = container['style']
        match = re.search(r'background-image:\s*url\("(.+?)"\)', style)
        return match.group(1) if match else "N/A"
    
    elif parse_method == 'none':
        container_tag, container_attrs = next(iter(img_config['container'].items()))
        container = item.find(container_tag, **container_attrs)
        if not container:
            return "N/A"
        img_element = container.find(img_config['tag'])
        return img_element.get(img_config['attr']) if img_element else "N/A"
    
    return "N/A"

def extract_location(item, config):
    location_tag, location_attrs = next(iter(config.get('location', {}).items()), (None, None))
    if not location_tag:
        return "N/A"
    
    parent_class = config.get('location', {}).get('parent', {}).get('class')
    parent_element = item.find('div', class_=parent_class) if parent_class else item
    
    location_elements = parent_element.find_all(location_tag, **location_attrs) if location_attrs else parent_element.find_all(location_tag)
    return " | ".join([loc.text.strip() for loc in location_elements]) if location_elements else "N/A"

def extract_recurrence(item, config):
    recurrence_tag, recurrence_attrs = next(iter(config.get('recurrence', {}).items()), (None, None))
    if not recurrence_tag:
        return "N/A"
    
    recurrence_element = item.find(recurrence_tag, **recurrence_attrs) if recurrence_attrs else item.find(recurrence_tag)
    return recurrence_element.text.strip() if recurrence_element else "N/A"

def extract_category(item, config):
    category_tag, category_attrs = next(iter(config.get('category', {}).items()), (None, None))
    if not category_tag:
        return "N/A"
    
    category_elements = item.find_all(category_tag, **category_attrs) if category_attrs else item.find_all(category_tag)
    return [cat.text.strip() for cat in category_elements] if category_elements else ["N/A"]

def extract_details(item, config):
    details_tag, details_attrs = next(iter(config.get('details', {}).items()), (None, None))
    if not details_tag:
        return "N/A"
    
    details_element = item.find(details_tag, **details_attrs) if details_attrs else item.find(details_tag)
    if not details_element:
        return "N/A"
    
    details_text = ' '.join(details_element.stripped_strings)
    return details_text if details_text else "N/A"


####################
# main extraction
####################

def extract_events(parsed_content, config):
    events = []
    content_list_tag, content_list_attrs = next(iter(config['content_list_class'].items()))
    content_list = parsed_content.find(content_list_tag, **content_list_attrs) if content_list_attrs else parsed_content
    
    if not content_list:
        logging.error("Couldn't find content list")
        return events

    item_tag, item_attrs = next(iter(config['item_attr'].items()))
    items = content_list.find_all(item_tag, **item_attrs) if item_attrs else content_list.find_all(item_tag)

    for item in items:
        title, title_element = extract_title(item, config)
        event = {}
        event['title'] = title
        event['details'] = extract_details(item, config)        
        event['date'], event['time'] = extract_date_and_time(item, config)
        event['location'] = extract_location(item, config)
        event['url'] = extract_event_url(item, title_element, config)
        event['image_url'] = extract_image_url(item, config)
        
        # event['recurrence'] = extract_recurrence(item, config)
        # event['category'] = extract_category(item, config)
        
        events.append(event)
    
    return events
 



####################
# EXECUTION
####################

def create_all_events_dataframe(all_events):
    all_df = pd.DataFrame()
    for site_name, events in all_events.items():
        df = pd.DataFrame(events)
        df['source'] = site_name
        all_df = pd.concat([all_df, df], ignore_index=True)
    return all_df

def save_all_events_to_csv(all_df, filename="all_events.csv"):
    all_df.to_csv(filename, index=False)

def main():
    all_events = {}
    for site_name, config in SITES.items():
        url = config["url"]
        logging.info("#" * 80)
        logging.info(f"Fetching and parsing {site_name}")
        logging.info("#" * 80)
        html_content, driver = fetch_page(url)
        if html_content:
            if execute_debugging:
                logging.info("=" * 80)
                grid_search(html_content)
                logging.info("=" * 80)
                find_iframes(html_content)
                logging.info("=" * 80)
                # check_shadow_dom(driver)
                # find_potential_containers(parsed_content)
                # capture_network_requests(site_name, driver)
                save_html(html_content, site_name)
            parsed_content = parse_html(html_content)
            if execute_save_html:
                save_parsed(parsed_content, site_name)

            events = extract_events(parsed_content, config)
            all_events[site_name] = events

            if execute_save_events_to_csv:
                save_events_to_csv(events, site_name)

            logging.info(f"Extracted {len(events)} events from {site_name}")
            for event in events:
                logging.info(f"Title: {event.get('title')}")
                logging.info(f"Image URL: {event.get('image_url')}")

                logging.info("-" * 40)

        else:
            logging.error(f"Failed to fetch or parse the content from {site_name}")

    # Create a single dataframe with all events
    all_events_df = create_all_events_dataframe(all_events)
    
    # Save the dataframe to a CSV file
    save_all_events_to_csv(all_events_df)


if __name__ == "__main__":
    main()


####################
# BUGS & TODOS
####################

# TODO: refactor date extraction to reduce redundant code

# TODO: add a price function 

# TODO: display image link as an image instead of a url

# TODO: fix capture network requests

# TODO: refactor debugging calls

# TODO: do i need the chromedriver install statements? should i setup a new env and kernel for this script? containerize it?

# BUG: script fails to establish connection (red herring?) when extracting shadow content on times free press

# TODO: get past lightbox (choose chatt, nooga today)

# TODO: i have two versions of CHA guide. only need one most likely

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
- implimented create_all_events_dataframe and save_all_events_to_csv functions
---

# 8-19-24

- set up script for debugging and fine-tuning url extraction
- fixed url extraction for:
    - visit chattanooga
    - chatt library
---

# 8-20-24

- fixed url extraction for:
    - CHA Guide Events
    - Chattanooga Pulse
    - CHA Guide Things To Do

- spent time on url extraction for Chattanooga Chamber
    - failed to extract url but fixed bug of only populating 5 events

- set up script for debugging date and time
- refactored date funtion to use parse_method
---

# 8-23-24
- date and time fixed for:
    - Visit Chattanooga
    - CHA Guide Events
    - Chattanooga Pulse
    - Chatt Library
- set up parse_method and extract_method
    - parse_method
        - parser.parse
        - time_range
        - split
        - split '@'
    - extract_method
        - attrs
        - tag
- set up script for debugging image extraction

'''