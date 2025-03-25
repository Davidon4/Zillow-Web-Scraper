import os
import csv
import requests
from bs4 import BeautifulSoup
import re
import time
import random
import json
from urllib.parse import quote, urlencode
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure retry strategy
retry_strategy = Retry(
    total=5,  # number of retries
    backoff_factor=0.5,  # wait 0.5 * (2 ** retry) seconds between retries
    status_forcelist=[500, 502, 503, 504, 429]  # HTTP status codes to retry on
)

def get_free_proxies():
    """Get a list of free proxies"""
    proxies = []
    try:
        # Get proxies from free-proxy-list.net
        response = requests.get('https://free-proxy-list.net/')
        soup = BeautifulSoup(response.text, 'html.parser')
        proxy_table = soup.find('table')
        
        if proxy_table:
            for row in proxy_table.find_all('tr')[1:]:  # Skip header row
                columns = row.find_all('td')
                if len(columns) >= 7:
                    ip = columns[0].text.strip()
                    port = columns[1].text.strip()
                    https = columns[6].text.strip()
                    
                    if https == 'yes':  # Only use HTTPS proxies
                        proxy = f'http://{ip}:{port}'
                        proxies.append(proxy)
        
        print(f"Found {len(proxies)} free proxies")
        return proxies
    except Exception as e:
        print(f"Error fetching free proxies: {e}")
        return []

def test_proxy(proxy):
    """Test if a proxy is working"""
    try:
        response = requests.get(
            'https://www.rightmove.co.uk',
            proxies={'http': proxy, 'https': proxy},
            timeout=10
        )
        return response.status_code == 200
    except:
        return False

def get_working_proxy():
    """Get a working proxy from the free proxy list"""
    proxies = get_free_proxies()
    for proxy in proxies:
        print(f"Testing proxy: {proxy}")
        if test_proxy(proxy):
            print(f"Found working proxy: {proxy}")
            return proxy
    return None

# Create session with retry strategy
def create_session(proxy=None):
    """
    Create a session with retry strategy and optional proxy
    
    Args:
        proxy (str): Optional proxy URL
    """
    session = requests.Session()
    
    # Configure proxy if provided
    if proxy:
        session.proxies = {
            'http': proxy,
            'https': proxy
        }
    
    adapter = HTTPAdapter(max_retries=retry_strategy, pool_maxsize=10)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

# More realistic browser headers
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-GB,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'sec-ch-ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-User': '?1',
    'Sec-Fetch-Dest': 'document',
    'Referer': 'https://www.rightmove.co.uk/',
    'DNT': '1'
}

def get_random_user_agent():
    """Return a random user agent to avoid detection"""
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Edge/121.0.2277.83 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0'
    ]
    return random.choice(user_agents)

def make_request(session, url, max_retries=3, initial_delay=15):
    """Make a request with exponential backoff retry logic"""
    for attempt in range(max_retries):
        try:
            current_headers = headers.copy()
            current_headers['User-Agent'] = get_random_user_agent()
            
            # Add random delay between requests
            delay = initial_delay * (2 ** attempt) + random.uniform(5, 15)
            print(f"Waiting {delay:.2f} seconds before making request...")
            time.sleep(delay)
            
            response = session.get(url, headers=current_headers, timeout=60)
            response.raise_for_status()
            
            time.sleep(random.uniform(2, 5))
            return response
            
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
            if attempt == max_retries - 1:
                # Try to get a new proxy if the current one fails
                if session.proxies:
                    print("Attempting to get a new proxy...")
                    new_proxy = get_working_proxy()
                    if new_proxy:
                        print(f"Switching to new proxy: {new_proxy}")
                        session.proxies = {'http': new_proxy, 'https': new_proxy}
                        continue
                raise
            print(f"Retrying in {delay:.2f} seconds...")
            time.sleep(random.uniform(10, 20))
            
    return None

def scrape_property_details(session, property_url):
    """
    Scrape detailed information about a property from its details page
    
    Args:
        session (requests.Session): Active session
        property_url (str): URL of the property details page
    
    Returns:
        dict: Dictionary containing detailed property information
    """
    details = {
        'url': property_url,
        'property_type': 'for-sale'
    }
    
    try:
        # Add random delay
        delay = random.uniform(3, 6)
        time.sleep(delay)
        
        # Update headers with random user agent
        current_headers = headers.copy()
        current_headers['User-Agent'] = get_random_user_agent()
        
        print(f"Fetching property details from: {property_url}")
        response = session.get(property_url, headers=current_headers, timeout=15)
        response.raise_for_status()
        
        # Save the HTML for debugging
        property_id = re.search(r'/properties/(\d+)', property_url)
        if property_id:
            property_id = property_id.group(1)
            details['property_id'] = property_id
        else:
            property_id = "unknown"
            
        with open(f"rightmove_property_{property_id}.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract property title (e.g., "3 bedroom semi-detached house for sale")
        title_elem = soup.select_one('h1.property-header-title, [data-testid="property-title"], .property-header h1')
        if title_elem:
            details['property_title'] = title_elem.text.strip()
        
        # Extract address
        address_elem = soup.select_one('.property-header-address, [data-testid="address-title"], .property-header address')
        if address_elem:
            details['address'] = address_elem.text.strip()
        
        # Extract Google Maps location
        map_elem = soup.select_one('#propertyMap, [data-testid="property-map"]')
        if map_elem:
            # Try to extract latitude and longitude
            lat_match = re.search(r'latitude["\s:=]+([0-9.-]+)', str(soup))
            lng_match = re.search(r'longitude["\s:=]+([0-9.-]+)', str(soup))
            if lat_match and lng_match:
                lat = lat_match.group(1)
                lng = lng_match.group(1)
                details['latitude'] = lat
                details['longitude'] = lng
                details['google_map_location'] = f"https://maps.googleapis.com/maps/api/staticmap?size=600x200&format=jpg&scale=1&center={lat},{lng}&maptype=roadmap&zoom=15&markers=scale:1%7C{lat},{lng}"
        
        # Check for virtual tour
        virtual_tour_elem = soup.find(string=re.compile('virtual tour', re.IGNORECASE))
        if virtual_tour_elem:
            parent = virtual_tour_elem.parent
            if parent:
                link = parent.find('a')
                if link and 'href' in link.attrs:
                    details['virtual_tour'] = link['href']
                else:
                    details['virtual_tour'] = "Available (link not found)"
            else:
                details['virtual_tour'] = "Available (link not found)"
        else:
            details['virtual_tour'] = ""
        
        # Street View
        if 'latitude' in details and 'longitude' in details:
            details['street_view'] = f"https://www.google.com/maps/@{details['latitude']},{details['longitude']},0a,73.7y,90t/data=!3m4!1e1!3m2!1s!2e0?source=apiv3"
        
        # Currency
        details['currency'] = 'GBP'
        
        # Property description
        description_elem = soup.select_one('#property-description, [data-testid="property-description"], .sect-wrap .sect')
        if description_elem:
            # Get all paragraphs
            paragraphs = description_elem.find_all('p')
            description_text = []
            for p in paragraphs:
                text = p.text.strip()
                if text:
                    description_text.append(text)
            details['description'] = description_text
        
        # Key features
        key_features = []
        features_elem = soup.select_one('#key-features, [data-testid="key-features"], .key-features')
        if features_elem:
            feature_items = features_elem.select('li')
            for item in feature_items:
                key_features.append(item.text.strip())
            details['features'] = key_features
        
        # Floor area
        floor_area_elem = soup.find(string=re.compile(r'([\d,.]+)\s*sq\s*ft|m²', re.IGNORECASE))
        if floor_area_elem:
            area_match = re.search(r'([\d,.]+)\s*sq\s*ft|m²', floor_area_elem, re.IGNORECASE)
            if area_match:
                details['property_size'] = f"{area_match.group(1).replace(',', '')}sq. ft"
        
        # EPC rating
        epc_elem = soup.select_one('[data-testid="epc-rating"], .epc-rating, .energy-rating')
        if epc_elem:
            details['ecp_rating'] = epc_elem.text.strip()
        
        # EPC certificate image
        epc_img = soup.select_one('.epc-graph img, [data-testid="epc-graph"] img')
        if epc_img and 'src' in epc_img.attrs:
            src = epc_img['src']
            if src.startswith('//'):
                src = 'https:' + src
            details['energy_performance_certificate'] = src
        
        # Council tax band
        tax_band_elem = soup.find(string=re.compile(r'Council Tax Band', re.IGNORECASE))
        if tax_band_elem:
            tax_match = re.search(r'Council Tax Band\s*([A-Z])', str(tax_band_elem), re.IGNORECASE)
            if tax_match:
                details['council_tax_band'] = tax_match.group(1)
        
        # Tenure (Freehold/Leasehold)
        tenure_elem = soup.find(string=re.compile(r'(Freehold|Leasehold)', re.IGNORECASE))
        if tenure_elem:
            tenure_match = re.search(r'(Freehold|Leasehold)', str(tenure_elem), re.IGNORECASE)
            if tenure_match:
                details['tenure'] = tenure_match.group(1)
                
            # If leasehold, try to find years remaining
            if 'leasehold' in str(tenure_elem).lower():
                years_match = re.search(r'(\d+)\s*years', str(soup), re.IGNORECASE)
                if years_match:
                    details['tenure'] = f"Leasehold ({years_match.group(1)} years)"
                    details['time_remaining_on_lease'] = f"{years_match.group(1)} years"
        
        # Service charge and ground rent
        service_charge_elem = soup.find(string=re.compile(r'service charge', re.IGNORECASE))
        if service_charge_elem:
            service_match = re.search(r'£([\d,.]+)(?:\s*per\s*(\w+))?', str(service_charge_elem), re.IGNORECASE)
            if service_match:
                amount = service_match.group(1)
                period = service_match.group(2) or 'year'
                details['service_charge'] = f"£{amount} per {period}"
        
        ground_rent_elem = soup.find(string=re.compile(r'ground rent', re.IGNORECASE))
        if ground_rent_elem:
            ground_match = re.search(r'£([\d,.]+)(?:\s*per\s*(\w+))?', str(ground_rent_elem), re.IGNORECASE)
            if ground_match:
                amount = ground_match.group(1)
                period = ground_match.group(2) or 'year'
                details['ground_rent'] = f"£{amount} per {period}"
        
        # Price per square foot
        if 'property_size' in details and 'price' in details:
            try:
                size = float(details['property_size'].replace('sq. ft', '').strip())
                price = float(details.get('price', 0))
                if size > 0 and price > 0:
                    price_per_sqft = round(price / size)
                    details['price_per_size'] = f"£{price_per_sqft:,}/sq. ft"
            except (ValueError, TypeError):
                pass
        
        # Agent details
        agent_details = {}
        agent_elem = soup.select_one('[data-testid="agent-name"], .agent-name, .agent-details .agent-name')
        if agent_elem:
            agent_details['agent_name'] = agent_elem.text.strip()
            
        agent_phone_elem = soup.select_one('[data-testid="agent-phone"], .agent-phone, .agent-details .agent-phone')
        if agent_phone_elem:
            agent_details['agent_phone'] = agent_phone_elem.text.strip()
        
        agent_logo = soup.select_one('.agent-logo img, [data-testid="agent-logo"] img')
        if agent_logo and 'src' in agent_logo.attrs:
            src = agent_logo['src']
            if src.startswith('//'):
                src = 'https:' + src
            agent_details['agent_logo'] = src
        
        if agent_details:
            details['agent_details'] = json.dumps(agent_details)
        
        # Similar properties
        similar_properties = []
        similar_section = soup.select_one('#similarProperties, [data-testid="similar-properties"], .similar-properties')
        if similar_section:
            similar_items = similar_section.select('.propertyCard, [data-testid="property-card"], .property-card')
            for item in similar_items[:5]:  # Limit to 5 similar properties
                similar_prop = {}
                
                # Extract price
                price_elem = item.select_one('.propertyCard-priceValue, [data-testid="property-price"], .price')
                if price_elem:
                    similar_prop['price'] = price_elem.text.strip()
                
                # Extract address
                address_elem = item.select_one('address, [data-testid="address-title"], .address')
                if address_elem:
                    similar_prop['address'] = address_elem.text.strip()
                
                # Extract link
                link_elem = item.select_one('a[href*="/properties/"], a[href*="/property-for-sale/"]')
                if link_elem and 'href' in link_elem.attrs:
                    href = link_elem['href']
                    if href.startswith('/'):
                        similar_prop['link'] = 'https://www.rightmove.co.uk' + href
                    else:
                        similar_prop['link'] = href
                
                if similar_prop:
                    similar_properties.append(similar_prop)
            
            details['similar_properties'] = similar_properties
        
        # Location information and points of interest
        points_of_interest = []
        
        # Nearby schools
        schools_section = soup.select_one('#schools, [data-testid="schools"], .schools')
        if schools_section:
            school_items = schools_section.select('.school-item, [data-testid="school-item"]')
            for school in school_items[:5]:  # Limit to 5 schools
                school_info = {}
                name_elem = school.select_one('.school-name, [data-testid="school-name"]')
                distance_elem = school.select_one('.school-distance, [data-testid="school-distance"]')
                
                if name_elem:
                    point = name_elem.text.strip()
                    distance = distance_elem.text.strip() if distance_elem else "Unknown"
                    points_of_interest.append({"point": point, "distance": distance})
        
        # Nearby stations
        stations_section = soup.select_one('#stations, [data-testid="stations"], .stations')
        if stations_section:
            station_items = stations_section.select('.station-item, [data-testid="station-item"]')
            for station in station_items[:5]:  # Limit to 5 stations
                name_elem = station.select_one('.station-name, [data-testid="station-name"]')
                distance_elem = station.select_one('.station-distance, [data-testid="station-distance"]')
                
                if name_elem:
                    point = name_elem.text.strip()
                    distance = distance_elem.text.strip() if distance_elem else "Unknown"
                    points_of_interest.append({"point": point, "distance": distance})
        
        if points_of_interest:
            details['points_ofInterest'] = json.dumps(points_of_interest)
        
        # Images
        image_urls = []
        image_elements = soup.select('img[src*="/media/"], [data-testid="gallery-image"] img, .gallery-thumbs img')
        for img in image_elements:
            if 'src' in img.attrs and '/media/' in img['src']:
                image_url = img['src']
                # Convert thumbnail URLs to full-size images
                image_url = re.sub(r'_max_\d+x\d+', '_max_1800x1800', image_url)
                image_urls.append(image_url)
        
        if image_urls:
            details['property_images'] = json.dumps(list(set(image_urls[:16])))  # Remove duplicates and limit to 16 images
        
        # Floor plans
        floor_plans = []
        floor_plan_elements = soup.select('.floorplan-img img, [data-testid="floorplan-image"] img')
        for img in floor_plan_elements:
            if 'src' in img.attrs:
                src = img['src']
                if src.startswith('//'):
                    src = 'https:' + src
                floor_plans.append(src)
        
        if floor_plans:
            details['floor_plans'] = json.dumps(floor_plans)
        
        # Listing history
        listing_history = []
        history_section = soup.select_one('#historyMarket, [data-testid="listing-history"]')
        if history_section:
            # Try to find when the property was first listed
            first_listed = soup.find(string=re.compile(r'Added on|Listed on', re.IGNORECASE))
            if first_listed:
                date_match = re.search(r'(\d{1,2}(?:st|nd|rd|th)?\s+\w+\s+\d{4})', str(first_listed), re.IGNORECASE)
                if date_match:
                    listing_date = date_match.group(1)
                    listing_history.append({
                        "event_type": "First listed",
                        "date": listing_date,
                        "price": details.get('price', 'Unknown'),
                        "currency": "£"
                    })
            
            # Try to find previous sale history
            sold_history = soup.find_all(string=re.compile(r'sold for|sold in', re.IGNORECASE))
            for sold in sold_history:
                price_match = re.search(r'£([\d,]+)', str(sold))
                date_match = re.search(r'(\d{1,2}(?:st|nd|rd|th)?\s+\w+\s+\d{4}|\w+\s+\d{4})', str(sold), re.IGNORECASE)
                
                if price_match and date_match:
                    listing_history.append({
                        "event_type": "Last sold",
                        "date": date_match.group(1),
                        "price": price_match.group(1),
                        "currency": "£"
                    })
        
        if listing_history:
            details['listing_history'] = json.dumps(listing_history)
        
        # Breadcrumbs
        breadcrumbs = []
        breadcrumb_elements = soup.select('.breadcrumb a, [data-testid="breadcrumb"] a')
        for crumb in breadcrumb_elements:
            if crumb.text.strip() and 'href' in crumb.attrs:
                href = crumb['href']
                if href.startswith('/'):
                    href = 'https://www.rightmove.co.uk' + href
                breadcrumbs.append({
                    "name": crumb.text.strip(),
                    "url": href
                })
        
        # Add current page to breadcrumbs
        if breadcrumbs and 'property_title' in details:
            breadcrumbs.append({
                "name": details['property_title'],
                "url": "https://www.rightmove.co.uk/null"
            })
            
        if breadcrumbs:
            details['breadcrumbs'] = json.dumps(breadcrumbs)
        
        # Extract bedrooms, bathrooms, and receptions
        if 'property_title' in details:
            beds_match = re.search(r'(\d+)\s*bed', details['property_title'], re.IGNORECASE)
            if beds_match:
                details['bedrooms'] = int(beds_match.group(1))
        
        # Try to find bathrooms in description or features
        bath_found = False
        if 'description' in details:
            for desc in details['description']:
                bath_match = re.search(r'(\d+)\s*bath', desc, re.IGNORECASE)
                if bath_match:
                    details['bathrooms'] = int(bath_match.group(1))
                    bath_found = True
                    break
        
        if not bath_found and 'features' in details:
            for feature in details['features']:
                bath_match = re.search(r'(\d+)\s*bath', feature, re.IGNORECASE)
                if bath_match:
                    details['bathrooms'] = int(bath_match.group(1))
                    break
        
        # Try to find receptions in description or features
        reception_found = False
        if 'description' in details:
            for desc in details['description']:
                reception_match = re.search(r'(\d+)\s*reception', desc, re.IGNORECASE)
                if reception_match:
                    details['receptions'] = reception_match.group(1)
                    reception_found = True
                    break
        
        if not reception_found and 'features' in details:
            for feature in details['features']:
                reception_match = re.search(r'(\d+)\s*reception', feature, re.IGNORECASE)
                if reception_match:
                    details['receptions'] = reception_match.group(1)
                    break
        
        # Market stats
        market_stats = {}
        
        # Average price in area
        avg_price_elem = soup.find(string=re.compile(r'average\s+price', re.IGNORECASE))
        if avg_price_elem:
            avg_match = re.search(r'£([\d,]+)', str(avg_price_elem))
            if avg_match:
                market_stats['average_estimated'] = f"£{avg_match.group(1)}"
        
        # Properties sold
        sold_elem = soup.find(string=re.compile(r'properties sold', re.IGNORECASE))
        if sold_elem:
            sold_match = re.search(r'(\d+)\s+properties sold', str(sold_elem), re.IGNORECASE)
            if sold_match:
                market_stats['properties_sold'] = sold_match.group(1)
        
        if market_stats:
            details['market_stats_last_12_months'] = json.dumps(market_stats)
        
        # Recent sales nearby
        recent_sales = []
        sales_section = soup.select_one('#recentlySold, [data-testid="recently-sold"]')
        if sales_section:
            sale_items = sales_section.select('.sold-property-item, [data-testid="sold-property"]')
            for sale in sale_items[:3]:  # Limit to 3 recent sales
                sale_info = {}
                
                address_elem = sale.select_one('.address, [data-testid="address"]')
                if address_elem:
                    sale_info['address'] = address_elem.text.strip()
                
                price_elem = sale.select_one('.price, [data-testid="price"]')
                if price_elem:
                    sale_info['price'] = price_elem.text.strip()
                
                date_elem = sale.select_one('.date, [data-testid="date"]')
                if date_elem:
                    sale_info['date'] = date_elem.text.strip()
                
                if sale_info:
                    recent_sales.append(sale_info)
            
            if recent_sales:
                details['market_stats_recent_sales_nearby'] = json.dumps(recent_sales)
        
        # Rental opportunities
        rental_elem = soup.find(string=re.compile(r'average\s+rent', re.IGNORECASE))
        if rental_elem:
            rent_match = re.search(r'£([\d,]+)\s+pcm', str(rental_elem), re.IGNORECASE)
            if rent_match:
                details['market_stats_renta_opportunities'] = f"£{rent_match.group(1)} pcm"
        
        # Country code
        details['country_code'] = "GB"
        
        # Extract tags from features
        if 'features' in details:
            details['tags'] = json.dumps(details['features'])
        
        # Additional links (brochures, etc.)
        additional_links = []
        brochure_links = soup.select('a[href*=".pdf"], a[href*="brochure"], a[href*="floorplan"]')
        for link in brochure_links:
            if 'href' in link.attrs:
                href = link['href']
                if href.startswith('/'):
                    href = 'https://www.rightmove.co.uk' + href
                additional_links.append(href)
        
        if additional_links:
            details['additional_links'] = json.dumps(additional_links)
        
        # Availability
        availability_elem = soup.find(string=re.compile(r'available from', re.IGNORECASE))
        if availability_elem:
            date_match = re.search(r'available from\s*(\d{1,2}(?:st|nd|rd|th)?\s+\w+\s+\d{4}|\w+\s+\d{4})', str(availability_elem), re.IGNORECASE)
            if date_match:
                details['availability'] = f"Available from{date_match.group(1)}"
        
        # Commonhold details
        commonhold_elem = soup.find(string=re.compile(r'commonhold', re.IGNORECASE))
        if commonhold_elem:
            details['commonhold_details'] = commonhold_elem.text.strip()
        
        # UPRN (Unique Property Reference Number)
        uprn_elem = soup.find(string=re.compile(r'UPRN', re.IGNORECASE))
        if uprn_elem:
            uprn_match = re.search(r'UPRN\s*:?\s*(\d+)', str(uprn_elem), re.IGNORECASE)
            if uprn_match:
                details['uprn'] = uprn_match.group(1)
        
        return details
        
    except Exception as e:
        print(f"Error fetching property details: {e}")
        import traceback
        traceback.print_exc()
        return details

def scrape_rightmove(location, num_pages=5, fetch_details=True, max_details=10, proxy=None):
    """
    Scrape property listings from Rightmove
    
    Args:
        location (str): Location to search for properties
        num_pages (int): Number of pages to scrape
        fetch_details (bool): Whether to fetch detailed information for each property
        max_details (int): Maximum number of properties to fetch details for
        proxy (str): Optional proxy URL (e.g., 'http://username:password@proxy.com:8080')
    
    Returns:
        list: List of dictionaries containing property data
    """
    all_properties = []
    seen_property_ids = set()
    seen_property_urls = set()
    
    # Define known location identifiers for common locations
    location_identifiers = {
        "london": "REGION%5E87490",
        "manchester": "REGION%5E162",
        "birmingham": "REGION%5E162",
        "leeds": "REGION%5E787",
        "liverpool": "REGION%5E138",
        "sheffield": "REGION%5E181",
        "newcastle": "REGION%5E250",
        "bristol": "REGION%5E275",
        "nottingham": "REGION%5E389",
        "leicester": "REGION%5E156",
        "edinburgh": "REGION%5E475",
        "glasgow": "REGION%5E550",
        "aberdeen": "REGION%5E663",
        "dundee": "REGION%5E723",
        "cardiff": "REGION%5E409",
        "swansea": "REGION%5E461",
        "newport": "REGION%5E437",
        "belfast": "REGION%5E606",
        "derry": "REGION%5E853",
        "brighton": "REGION%5E1234",
        "brighton & hove": "REGION%5E1234",
        "hove": "REGION%5E1234",
        "southampton": "REGION%5E1235",
        "derby": "REGION%5E1236",
        "milton keynes": "REGION%5E1237",
        "bournemouth": "REGION%5E1238",
        "portsmouth": "REGION%5E1239",
        "york": "REGION%5E1240"
    }
    
    location_lower = location.lower().strip()
    location_id = location_identifiers.get(location_lower)
    
    session = create_session(proxy)
    
    try:
        print("Setting up session...")
        # Visit homepage first to get cookies
        response = make_request(session, 'https://www.rightmove.co.uk/')
        time.sleep(random.uniform(2, 4))
        
        if not location_id:
            print("Getting location identifier...")
            # Clean the location string for URL
            clean_location = location.replace('&', 'and').replace(',', '').strip()
            search_url = f"https://www.rightmove.co.uk/property-for-sale/search.html?searchLocation={quote(clean_location)}&useLocationIdentifier=true"
            response = make_request(session, search_url)
            
            match = re.search(r'locationIdentifier=([^&]+)', response.url)
            if match:
                location_id = match.group(1)
                print(f"Found location identifier: {location_id}")
            else:
                print("Could not find location identifier in URL")
                # Try a simpler search without location identifier
                search_url = f"https://www.rightmove.co.uk/property-for-sale/search.html?searchLocation={quote(clean_location)}"
                response = make_request(session, search_url)
                match = re.search(r'locationIdentifier=([^&]+)', response.url)
                if match:
                    location_id = match.group(1)
                    print(f"Found location identifier: {location_id}")
                else:
                    raise ValueError(f"Could not find location identifier for {location}")
        
        for page in range(num_pages):
            try:
                index = page * 24
                url = f"https://www.rightmove.co.uk/property-for-sale/find.html?searchType=SALE&locationIdentifier={location_id}&index={index}&propertyTypes=&includeSSTC=false&mustHave=&dontShow=&furnishTypes=&keywords="
                
                print(f"\nFetching page {page + 1}/{num_pages}")
                response = make_request(session, url)
                
                if not response:
                    print(f"Failed to fetch page {page + 1}")
                    continue
                
                # Save the HTML for debugging
                with open(f"rightmove_page_{page + 1}.html", "w", encoding="utf-8") as f:
                    f.write(response.text)
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find all property listings - use multiple selectors to catch different HTML structures
                listings = []
                
                # Try different selectors that might match property listings
                selectors = [
                    'div.propertyCard',
                    'div.l-searchResult',
                    'div[data-test="propertyCard"]',
                    'div.property-card'
                ]
                
                for selector in selectors:
                    listings = soup.select(selector)
                    if listings:
                        print(f"Found listings with selector: {selector}")
                        break
                
                if not listings:
                    print(f"No listings found on page {page + 1}. The page structure might have changed.")
                    continue
                
                print(f"Found {len(listings)} listings on page {page + 1}")
                
                # Process each listing
                page_properties = []
                duplicates_found = 0
                
                for listing in listings:
                    property_data = {}
                    
                    # Extract link first to check for duplicates
                    link_elem = listing.select_one('a.propertyCard-link, a.property-card-link, [data-test="property-details-link"]')
                    if not link_elem:
                        # Try to find any link that points to property details
                        link_elem = listing.find('a', href=lambda h: h and ('/properties/' in h or '/property-for-sale/' in h))
                    
                    if link_elem and 'href' in link_elem.attrs:
                        href = link_elem['href']
                        if href.startswith('/'):
                            property_url = 'https://www.rightmove.co.uk' + href
                        else:
                            property_url = href
                        
                        # Extract property ID from URL
                        property_id_match = re.search(r'/properties/(\d+)', property_url)
                        property_id = property_id_match.group(1) if property_id_match else None
                        
                        # Check if we've already seen this property
                        if property_url in seen_property_urls or (property_id and property_id in seen_property_ids):
                            duplicates_found += 1
                            continue
                        
                        # Add to tracking sets
                        seen_property_urls.add(property_url)
                        if property_id:
                            seen_property_ids.add(property_id)
                            
                        property_data['link'] = property_url
                        if property_id:
                            property_data['property_id'] = property_id
                    else:
                        # Skip if we can't find a link - we need it to check for duplicates
                        continue
                    
                    # Extract price
                    price_elem = listing.select_one('.propertyCard-priceValue, .property-card-price, [data-test="property-price"]')
                    if price_elem:
                        property_data['price'] = price_elem.text.strip()
                    
                    # Extract address
                    address_elem = listing.select_one('address.propertyCard-address, .property-card-address, [data-test="address-title"]')
                    if address_elem:
                        property_data['address'] = address_elem.text.strip()
                    
                    # Extract property type and bedrooms
                    title_elem = listing.select_one('h2.propertyCard-title, .property-card-title, [data-test="property-title"]')
                    if title_elem:
                        title_text = title_elem.text.strip()
                        # Usually in format: "3 bedroom semi-detached house for sale"
                        beds_match = re.search(r'(\d+)\s*bedroom', title_text, re.IGNORECASE)
                        property_data['beds'] = beds_match.group(1) if beds_match else '0'
                        
                        # Extract property type
                        type_match = re.search(r'bedroom\s+([^for]+)', title_text, re.IGNORECASE)
                        if type_match:
                            property_data['type'] = type_match.group(1).strip()
                        else:
                            property_data['type'] = 'Not specified'
                    
                    # Extract description snippet
                    desc_elem = listing.select_one('.propertyCard-description, .property-card-description, [data-test="property-description"]')
                    if desc_elem:
                        property_data['description'] = desc_elem.text.strip()
                        
                        # Try to extract bathroom count from description
                        bath_match = re.search(r'(\d+)\s*bathroom', property_data.get('description', ''), re.IGNORECASE)
                        property_data['baths'] = bath_match.group(1) if bath_match else '0'
                    
                    # Extract agent
                    agent_elem = listing.select_one('.propertyCard-branchSummary, .property-card-agent, [data-test="agent-name"]')
                    if agent_elem:
                        property_data['agent'] = agent_elem.text.strip()
                    
                    # Extract date added
                    date_elem = listing.select_one('.propertyCard-contactsAddedOrReduced, .property-card-date, [data-test="date-added"]')
                    if date_elem:
                        property_data['date_added'] = date_elem.text.strip()
                    
                    if property_data:
                        page_properties.append(property_data)
                
                all_properties.extend(page_properties)
                print(f"Successfully processed {len(page_properties)} properties from page {page + 1}")
                if duplicates_found > 0:
                    print(f"Skipped {duplicates_found} duplicate properties on page {page + 1}")
                
                if not page_properties:
                    print("No new properties found on this page. Stopping search.")
                    break
                
            except requests.exceptions.RequestException as e:
                print(f"Error fetching page {page + 1}: {e}")
                continue
            except Exception as e:
                print(f"Unexpected error on page {page + 1}: {e}")
                import traceback
                traceback.print_exc()
                continue
    except Exception as e:
        print(f"Error during scraping: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print(f"Total unique properties found: {len(all_properties)}")
        
        # Clean up data
        for prop in all_properties:
            if 'price' in prop:
                # Extract numeric price value
                price_text = prop['price']
                price_match = re.search(r'£?([\d,]+)', price_text)
                if price_match:
                    prop['price'] = price_match.group(1).replace(',', '')
    
    # Fetch detailed information for each property
    if fetch_details and all_properties:
        print("\nFetching detailed information for properties...")
        properties_with_details = []
        
        # Limit the number of properties to fetch details for
        properties_to_process = all_properties[:max_details]
        
        for i, prop in enumerate(properties_to_process):
            if 'link' in prop:
                print(f"Fetching details for property {i+1}/{len(properties_to_process)}...")
                details = scrape_property_details(session, prop['link'])
                # Merge the details with the property data
                prop.update(details)
            properties_with_details.append(prop)
        
        return properties_with_details
    
    return all_properties

def save_to_csv(properties, filename):
    """Save properties to a CSV file"""
    if not properties:
        print("No properties to save")
        return
    
    # Get all possible fields from all properties
    fieldnames = set()
    for prop in properties:
        fieldnames.update(prop.keys())
    
    # Remove complex fields that don't work well in CSV
    for field in ['similar_properties', 'image_urls', 'key_features', 'nearby_schools', 'nearby_stations']:
        if field in fieldnames:
            fieldnames.remove(field)
    
    fieldnames = sorted(list(fieldnames))
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        # Write rows, excluding complex fields
        for prop in properties:
            row = {k: v for k, v in prop.items() if k in fieldnames}
            writer.writerow(row)
    
    print(f"Saved {len(properties)} properties to {filename}")

def transform_to_uk_property_format(properties):
    """
    Transform scraped Rightmove properties to a uniform UKProperty format.
    Only includes properties that have all the required fields.
    
    UKProperty format:
    {
      id: string;
      address: string;
      price: number;
      bedrooms: number | null;
      bathrooms: number | null;
      square_feet: number | null;
      image_url: string | null;
      property_type?: string;
      description?: string;
      latitude?: number;
      longitude?: number;
      agent?: {
        name: string;
        phone: string;
      };
      created_at: string;
      updated_at: string;
      property_details?: {
        market_demand: string;
        area_growth: string;
        crime_rate: string;
        nearby_schools: number;
        energy_rating: string;
        council_tax_band: string;
        property_features: string[];
        tenure?: string;
        time_remaining_on_lease?: string;
      };
      listing_type: string;
    }
    """
    transformed_properties = []
    skipped_count = 0
    
    for prop in properties:
        # Check required fields before proceeding
        if not all(key in prop for key in ['property_id', 'address', 'price']):
            skipped_count += 1
            continue
            
        # Only process properties with valid numeric price
        try:
            price = int(prop.get('price', '0').replace(',', ''))
            if price <= 0:
                skipped_count += 1
                continue
        except (ValueError, TypeError):
            skipped_count += 1
            continue
        
        # Start building the property object with required fields
        uk_property = {
            "id": prop['property_id'],
            "address": prop['address'],
            "price": price,
            "listing_type": "for-sale"
        }
        
        # Only add fields that are actually present in the data
        
        # Bedrooms
        if 'beds' in prop and prop['beds'] and prop['beds'].isdigit():
            uk_property["bedrooms"] = int(prop['beds'])
            
        # Bathrooms
        if 'baths' in prop and prop['baths'] and prop['baths'].isdigit():
            uk_property["bathrooms"] = int(prop['baths'])
        
        # Date information
        if 'date_added' in prop and prop['date_added']:
            uk_property["created_at"] = prop['date_added']
            uk_property["updated_at"] = prop['date_added']
        
        # Property type
        if 'type' in prop and prop['type']:
            uk_property["property_type"] = prop['type']
        
        # Description
        if 'description' in prop and prop['description']:
            if isinstance(prop['description'], list):
                uk_property["description"] = ' '.join(prop['description'])
            else:
                uk_property["description"] = prop['description']
        
        # Coordinates
        if 'latitude' in prop and 'longitude' in prop:
            try:
                lat = float(prop['latitude'])
                long = float(prop['longitude'])
                uk_property["latitude"] = lat
                uk_property["longitude"] = long
            except (ValueError, TypeError):
                pass
        
        # Square feet from property_size
        if 'property_size' in prop and prop['property_size']:
            try:
                sq_ft = prop['property_size'].replace('sq. ft', '').strip()
                uk_property["square_feet"] = int(float(sq_ft))
            except (ValueError, TypeError):
                pass
        
        # Image URL
        if 'property_images' in prop and prop['property_images']:
            try:
                images = json.loads(prop['property_images']) if isinstance(prop['property_images'], str) else prop['property_images']
                if images and len(images) > 0:
                    uk_property["image_url"] = images[0]
            except (json.JSONDecodeError, TypeError):
                pass
        
        # Extract agent details - only if present
        agent_info = {}
        if 'agent' in prop and prop['agent']:
            agent_info["name"] = prop['agent']
        
        if 'agent_details' in prop and prop['agent_details']:
            try:
                agent_details = json.loads(prop['agent_details']) if isinstance(prop['agent_details'], str) else prop['agent_details']
                if 'agent_name' in agent_details and agent_details['agent_name']:
                    agent_info["name"] = agent_details['agent_name']
                if 'agent_phone' in agent_details and agent_details['agent_phone']:
                    agent_info["phone"] = agent_details['agent_phone']
            except (json.JSONDecodeError, TypeError, AttributeError):
                pass
        
        # Only add agent if we have valid data
        if agent_info and "name" in agent_info:
            if "phone" not in agent_info:
                # Don't add incomplete agent information
                continue
            uk_property["agent"] = agent_info
        
        # Build property details - only include fields that have real data
        property_details = {}
        
        # Tenure - only add if present
        if 'tenure' in prop and prop['tenure']:
            property_details["tenure"] = prop['tenure']
            
            # If it's leasehold, check for remaining years
            if 'leasehold' in prop['tenure'].lower() and 'years' in prop['tenure'].lower():
                years_match = re.search(r'(\d+)\s*years', prop['tenure'], re.IGNORECASE)
                if years_match:
                    property_details["time_remaining_on_lease"] = f"{years_match.group(1)} years"
        
        # Add time_remaining_on_lease if explicitly provided
        elif 'time_remaining_on_lease' in prop and prop['time_remaining_on_lease']:
            property_details["time_remaining_on_lease"] = prop['time_remaining_on_lease']
        
        # Energy rating
        if 'ecp_rating' in prop and prop['ecp_rating']:
            property_details["energy_rating"] = prop['ecp_rating']
        
        # Council tax band
        if 'council_tax_band' in prop and prop['council_tax_band']:
            property_details["council_tax_band"] = prop['council_tax_band']
        
        # Features
        if 'features' in prop and prop['features']:
            try:
                if isinstance(prop['features'], list) and prop['features']:
                    property_details["property_features"] = prop['features']
                elif isinstance(prop['features'], str) and prop['features']:
                    property_details["property_features"] = [prop['features']]
            except (TypeError, AttributeError):
                pass
        
        # Nearby schools count
        if 'points_ofInterest' in prop and prop['points_ofInterest']:
            try:
                poi = json.loads(prop['points_ofInterest']) if isinstance(prop['points_ofInterest'], str) else prop['points_ofInterest']
                if poi:
                    school_count = sum(1 for point in poi if 'school' in point.get('point', '').lower())
                    if school_count > 0:
                        property_details["nearby_schools"] = school_count
            except (json.JSONDecodeError, TypeError, AttributeError):
                pass
        
        # Market stats
        if 'market_stats_last_12_months' in prop and prop['market_stats_last_12_months']:
            try:
                market_stats = json.loads(prop['market_stats_last_12_months']) if isinstance(prop['market_stats_last_12_months'], str) else prop['market_stats_last_12_months']
                
                if market_stats:
                    if 'properties_sold' in market_stats and market_stats['properties_sold']:
                        sold_count = int(market_stats['properties_sold'])
                        property_details["market_demand"] = f"High ({sold_count} properties sold)" if sold_count > 10 else f"Low ({sold_count} properties sold)"
                    
                    if 'average_estimated' in market_stats and market_stats['average_estimated']:
                        avg_price_str = market_stats['average_estimated'].replace('£', '').replace(',', '')
                        try:
                            avg_price = int(avg_price_str)
                            if avg_price > 0 and price > 0:
                                percentage = ((price - avg_price) / avg_price) * 100
                                property_details["area_growth"] = f"{percentage:.1f}% {'above' if percentage > 0 else 'below'} average"
                        except (ValueError, TypeError):
                            pass
            except (json.JSONDecodeError, TypeError, ValueError, AttributeError):
                pass
        
        # Only add property details if we have real data
        if property_details:
            uk_property["property_details"] = property_details
        
        # After all processing, check if we have a valid property with minimum required fields
        if all(key in uk_property for key in ['id', 'address', 'price']):
            transformed_properties.append(uk_property)
        else:
            skipped_count += 1
    
    print(f"Transformed {len(transformed_properties)} properties. Skipped {skipped_count} properties due to incomplete data.")
    return transformed_properties

def display_properties(properties, num=5):
    """Display the first few properties"""
    if not properties:
        print("No properties to display")
        return
    
    print("\nFirst few properties:")
    for i, prop in enumerate(properties[:num]):
        print(f"\nProperty {i+1}:")
        for key, value in prop.items():
            if key not in ['similar_properties', 'image_urls', 'full_description', 'key_features', 'nearby_schools', 'nearby_stations']:
                print(f"  {key}: {value}")
        
        if 'similar_properties' in prop and prop['similar_properties']:
            print(f"  Similar properties: {len(prop['similar_properties'])} found")
        
        if 'image_urls' in prop and prop['image_urls']:
            print(f"  Images: {len(prop['image_urls'])} found")
        
        if 'key_features' in prop and prop['key_features']:
            print(f"  Key features: {len(prop['key_features'])} found")
        
        if 'nearby_schools' in prop and prop['nearby_schools']:
            print(f"  Nearby schools: {len(prop['nearby_schools'])} found")
        
        if 'nearby_stations' in prop and prop['nearby_stations']:
            print(f"  Nearby stations: {len(prop['nearby_stations'])} found")

if __name__ == "__main__":
    # Get list of locations to search
    locations_input = input("Enter locations to search (comma-separated, e.g., Southampton, Derby, Milton Keynes, Bournemouth, Portsmouth, York, Newport): ").strip()
    locations = [loc.strip() for loc in locations_input.split(',') if loc.strip()]
    
    if not locations:
        locations = ["Southampton", "Derby", "Milton Keynes", "Bournemouth", "Portsmouth", "York", "Newport"]
    
    try:
        num_pages = int(input("Enter number of pages to scrape per location (default 5): ") or "5")
    except ValueError:
        num_pages = 5
    
    try:
        fetch_details = input("Fetch detailed information for each property? (y/n, default: y): ").strip().lower() != 'n'
    except:
        fetch_details = True
    
    if fetch_details:
        try:
            max_details = int(input("Maximum number of properties to fetch details for per location (default 10): ") or "10")
        except ValueError:
            max_details = 10
    else:
        max_details = 0
    
    # Try to get a working proxy
    print("Searching for a working proxy...")
    proxy = get_working_proxy()
    if proxy:
        print(f"Using proxy: {proxy}")
    else:
        print("No working proxy found. Continuing without proxy...")
    
    all_properties = []
    all_transformed_properties = []
    
    for location in locations:
        print(f"\nScraping Rightmove for properties in {location}...")
        properties = scrape_rightmove(location, num_pages, fetch_details, max_details, proxy=proxy)
        
        if not properties:
            print(f"No properties found for {location}. Please check the location name or try again later.")
        else:
            # Transform to uniform format
            transformed_properties = transform_to_uk_property_format(properties)
            
            all_properties.extend(properties)
            all_transformed_properties.extend(transformed_properties)
            
            # Save individual location data (raw format)
            output_file = f"rightmove_{location.lower().replace(' ', '_')}_properties.csv"
            save_to_csv(properties, output_file)
            
            # Save transformed data (uniform format)
            json_file = f"rightmove_{location.lower().replace(' ', '_')}_properties.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(transformed_properties, f, indent=2)
            
            # Also save raw data as JSON for reference
            raw_json_file = f"rightmove_{location.lower().replace(' ', '_')}_properties_raw.json"
            with open(raw_json_file, 'w', encoding='utf-8') as f:
                json.dump(properties, f, indent=2)
                
            print(f"Data saved to {output_file}, {json_file}, and {raw_json_file}")
    
    if all_properties:
        # Save combined data (raw format)
        combined_csv = "rightmove_all_locations_properties.csv"
        save_to_csv(all_properties, combined_csv)
        
        # Save combined transformed data (uniform format)
        combined_json = "rightmove_all_locations_properties.json"
        with open(combined_json, 'w', encoding='utf-8') as f:
            json.dump(all_transformed_properties, f, indent=2)
            
        # Also save combined raw data as JSON for reference
        combined_raw_json = "rightmove_all_locations_properties_raw.json"
        with open(combined_raw_json, 'w', encoding='utf-8') as f:
            json.dump(all_properties, f, indent=2)
        
        print(f"\nTotal properties found across all locations: {len(all_properties)}")
        print(f"Combined data saved to {combined_csv}, {combined_json}, and {combined_raw_json}")
        
        # Display sample from each location
        print("\nSample properties from each location:")
        for location in locations:
            location_properties = [p for p in all_transformed_properties if p.get('address', '').lower().find(location.lower()) != -1]
            if location_properties:
                print(f"\n{location}:")
                display_properties(location_properties, 1)
    else:
        print("\nNo properties found in any location. Please check the location names or try again later.") 