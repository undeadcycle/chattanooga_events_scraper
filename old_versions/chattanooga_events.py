from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import chromedriver_autoinstaller
from bs4 import BeautifulSoup
from datetime import datetime
from dateutil import parser
import time
import re

####################
# CONFIGURATION
####################

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
    
    # "Nooga Today": {
    #     "url": "https://noogatoday.6amcity.com/events#/", # preloaded_lightbox blocking site
    #     },
    
    # "Choose Chatt": {
    #     "url": "https://choosechatt.com/chattanooga-events/", # dialog-lightbox-message blocking site
    # },

    "Times Free Press": {
        "url": "https://www.timesfreepress.com/tfpevents/?_evDiscoveryPath=/",
        "content_list_class": {"div": {"class": "grid"}},
        "item_attr": {"div": {"class": "c-card"}},
        "title": {"h3": {}},
        "date": {"div": {"class": "rounded-r"}},
        "img": {
            "img": {"class": "event-image"},
            "parse_method": "src"
        },
        "location": {"li": {"class": "line-clamp-1"}},
        "recurrence": None,  # No clear recurrence information in the provided HTML
        "time": {"li": {"class": None}},  # The first <li> element contains the time
        "price": {"li": None}  # The last <li> element contains the price
    },

    # "CHA Guide Weekly": {
    #     "url": "https://www.cha.guide/explore/things-to-do-in-chattanooga-this-week",
    # },

    # "Chattanooga Chamber": {
    #     "url": "https://chattanoogachamber.com/",
    # },

    # "Chattanooga Library": {
    #     "url": "https://www.chattlibrary.org/events/",
    # }

}

####################
# FETCHING & PARSING
####################

def fetch_page(url):
    # options = Options()
    # options.add_argument("--headless")  # Run in headless mode (no GUI)
    # service = Service(ChromeDriverManager().install())
    chromedriver_autoinstaller.install()
    driver = webdriver.Chrome()
    
    try:
        driver.get(url)
        time.sleep(5)  # Wait for JavaScript to load content
        check_shadow_dom(driver) #DEBUGGING
        scroll_page(driver) #DEBUGGING
        return driver.page_source
    except Exception as e:
        print(f"Error fetching the page: {e}")
        return None
    finally:
        driver.quit()

def parse_html(html_content):
    return BeautifulSoup(html_content, 'html.parser')

####################
# DEBUGGING 
####################

def grid_search(html_content):
    grid_match = re.search(r'<div[^>]*class="[^"]*grid[^"]*"', html_content)
    if grid_match:
        start = max(0, grid_match.start() - 500)
        end = min(len(html_content), grid_match.end() + 1000)
        print(html_content[start:end])
    else:
        print("Could not find 'grid' class in the HTML")

def find_iframes(html_content):
    iframes = parsed_content.find_all('iframe')
    for iframe in iframes:
        print(f"Found iframe: {iframe.get('src', 'No src attribute')}")

def check_shadow_dom(driver):
    shadow_hosts = driver.execute_script("""
        return Array.from(document.querySelectorAll('*')).filter(el => el.shadowRoot);
    """)
    for host in shadow_hosts:
        print(f"Found Shadow DOM host: {host.tag_name}, id: {host.get_attribute('id')}")

def find_potential_containers(parsed_content):
    potential_containers = parsed_content.find_all('div', class_=lambda x: x and any(keyword in x.lower() for keyword in ['list', 'container', 'wrapper', 'events']))
    for container in potential_containers:
        print(f"Potential container found: {container.get('class')}")

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
    
    # Add other parsing methods here if needed
    
    return None

def parse_date_range(date_text):
    # Regular expression to match date, start time, and end time
    pattern = r'(\w+ \d+, \d{4})(?: (\d+:\d+ [AP]M))?(?: - (\d+:\d+ [AP]M))?'
    match = re.match(pattern, date_text)
    
    if match:
        date_str, start_time, end_time = match.groups()
        
        try:
            # Parse the date
            parsed_date = parser.parse(date_str)
            date = parsed_date.strftime("%Y-%m-%d")
            
            # Parse start time if available
            start = None
            if start_time:
                start = parser.parse(f"{date_str} {start_time}").strftime("%H:%M")
            
            # Parse end time if available
            end = None
            if end_time:
                end = parser.parse(f"{date_str} {end_time}").strftime("%H:%M")
            
            return {
                'date': date,
                'start_time': start,
                'end_time': end
            }
        except ValueError:
            print(f"Couldn't parse date: {date_text}")
    
    return {
        'date': None,
        'start_time': None,
        'end_time': None
    }

# TODO: category function

# TODO: details function

def extract_events(parsed_content, config):
    events = []
    print(f"Searching for content list with: {config['content_list_class']}")
    
    # Unpack the content_list_class dictionary
    tag, class_name = next(iter(config['content_list_class'].items()))
    
    content_list = None
    
    # Try to find content list by id first
    try:
        if 'id' in class_name:
            content_list = parsed_content.find(tag, id=class_name['id'])
            print(f"Attempting to find content list by id: {class_name['id']}")
    except Exception as e:
        print(f"Error when searching by id: {e}")

    # If not found by id, try to find by class
    if not content_list:
        try:
            if 'class' in class_name:
                content_list = parsed_content.find(tag, class_=class_name['class'])
                print(f"Attempting to find content list by class: {class_name['class']}")
        except Exception as e:
            print(f"Error when searching by class: {e}")

    # If still not found, try to find without any attributes
    if not content_list:
        try:
            content_list = parsed_content.find(tag)
            print(f"Attempting to find content list by tag: {tag}")
        except Exception as e:
            print(f"Error when searching by tag: {e}")

    if not content_list:
        print("Couldn't find content list")
        return events

    # print(f"Found content list: {content_list}")

    # Unpack the item_attr dictionary
    item_tag, item_attrs = next(iter(config['item_attr'].items()))
    try:
        items = content_list.find_all(item_tag, **item_attrs)
        print(f"Found {len(items)} items with specified attributes")
    except Exception as e:
        print(f"Error when finding items: {e}")
        return events

    for item in items:
        event = {}
        
        # Extract title and URL
        try:
            title_tag, title_attrs = next(iter(config['title'].items()))
            title_element = item.find(title_tag, **title_attrs)
            if title_element:
                event['title'] = title_element.text.strip()
                url_element = title_element if title_element.name == 'a' else title_element.find_parent('a')
                event['url'] = config["url"] + url_element['href'] if url_element else ''
            else:
                print("Couldn't find title element")
                continue
        except Exception as e:
            print(f"Error extracting title: {e}")
            continue

        # Extract date and times
        try:
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
        except Exception as e:
            print(f"Error extracting date: {e}")

        # Extract image URL
        try:
            if config.get("img"):
                event['image_url'] = extract_image_url(config["img"], item)
            else:
                event['image_url'] = None
        except Exception as e:
            print(f"Error extracting image URL: {e}")
            event['image_url'] = None

        # Extract location
        try:
            location_tag, location_attrs = next(iter(config['location'].items()))
            location_element = item.find(location_tag, **location_attrs)
            event['location'] = location_element.text.strip() if location_element else None
        except Exception as e:
            print(f"Error extracting location: {e}")
            event['location'] = None

        # Extract recurrence information
        try:
            recurrence_tag, recurrence_attrs = next(iter(config['recurrence'].items()))
            recurrence_element = item.find(recurrence_tag, **recurrence_attrs)
            event['recurrence'] = recurrence_element.text.strip() if recurrence_element else None
        except Exception as e:
            print(f"Error extracting recurrence: {e}")
            event['recurrence'] = None

        events.append(event)
    
    return events

####################
# EXECUTION
####################

def main():
    for site_name, config in SITES.items():
        url = config["url"]
        print(f"Fetching and parsing {site_name}")

        html_content = fetch_page(url)
        if html_content:
            save_html(html_content, site_name) #DEBUGGING
            grid_search(html_content) #DEBUGGING
            
            parsed_content = parse_html(html_content)
            print(f"Length of parsed content: {len(str(parsed_content))}")
            find_potential_containers(parsed_content) # DEBUGGING
            # find_iframes(html_content) #DEBUGGING
            events = extract_events(parsed_content, config)
            print(f"Extracted {len(events)} events")
            for event in events:
                print(f"Title: {event.get('title')}")
                print(f"URL: {event.get('url')}")
                print(f"Date: {event.get('date')}")
                print(f"Start Time: {event.get('start_time')}")
                print(f"End Time: {event.get('end_time')}")
                print(f"Image URL: {event.get('image_url')}")
                print(f"Location: {event.get('location')}")
                print(f"Recurrence: {event.get('recurrence')}")
                print("-" * 40)
        else:
            print(f"Skipping {site_name} due to fetch error")
        time.sleep(1)  # Be polite, wait a second between requests

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
# Capture network requests
        # logs = driver.get_log('performance')
        # for log in logs:
        #     network_log = json.loads(log['message'])['message']
        #     if ('Network.response' in network_log['method'] 
        #         or 'Network.request' in network_log['method']
        #         or 'Network.webSocket' in network_log['method']):
        #         print(network_log)

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