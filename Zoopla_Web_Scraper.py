import os
import csv
import requests
from bs4 import BeautifulSoup
import re
import time
import random
import json
from urllib.parse import quote

# More realistic browser headers
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Cache-Control': 'max-age=0',
    'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-User': '?1',
    'Sec-Fetch-Dest': 'document',
    'Referer': 'https://www.zoopla.co.uk/',
    'DNT': '1'
}

def get_random_user_agent():
    """Return a random user agent to avoid detection"""
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.2 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:96.0) Gecko/20100101 Firefox/96.0',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36 Edg/96.0.1054.62',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 15_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.2 Mobile/15E148 Safari/604.1'
    ]
    return random.choice(user_agents)

def scrape_zoopla(location, num_pages=5):
    """
    Scrape property listings from Zoopla
    
    Args:
        location (str): Location to search for properties
        num_pages (int): Number of pages to scrape
    
    Returns:
        list: List of dictionaries containing property data
    """
    all_properties = []
    
    # Try alternative approach using the API
    print("Attempting to use alternative method...")
    try:
        properties = scrape_zoopla_api(location, num_pages)
        if properties:
            return properties
    except Exception as e:
        print(f"API method failed: {e}")
        print("Falling back to HTML scraping...")
    
    with requests.session() as s:
        # Set cookies and visit the homepage first
        try:
            print("Visiting homepage to set cookies...")
            s.get('https://www.zoopla.co.uk/', headers=headers, timeout=10)
            time.sleep(random.uniform(2, 4))
        except Exception as e:
            print(f"Error visiting homepage: {e}")
        
        for page in range(1, num_pages + 1):
            # Update headers with a random user agent for each request
            current_headers = headers.copy()
            current_headers['User-Agent'] = get_random_user_agent()
            
            # Format URL for the search - use encoded location
            encoded_location = quote(location.lower().replace(' ', '-'))
            url = f'https://www.zoopla.co.uk/for-sale/{encoded_location}/?page_size=25&q={location}&radius=0&results_sort=newest_listings&pn={page}'
            
            try:
                # Add random delay to avoid being blocked
                delay = random.uniform(5, 10)
                print(f"Waiting {delay:.2f} seconds before fetching page {page}...")
                time.sleep(delay)
                
                # Get the page
                print(f"Fetching page {page}...")
                response = s.get(url, headers=current_headers, timeout=15)
                
                if response.status_code == 403:
                    print(f"Access forbidden (403) for page {page}. Zoopla is blocking the scraper.")
                    continue
                
                response.raise_for_status()  # Raise exception for other HTTP errors
                
                # Parse the HTML
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Check for captcha or robot detection
                if "captcha" in response.text.lower() or "robot" in response.text.lower():
                    print("Captcha or robot detection encountered. Cannot proceed with scraping.")
                    with open(f"zoopla_captcha_page_{page}.html", "w", encoding="utf-8") as f:
                        f.write(str(soup))
                    print(f"Saved captcha page to zoopla_captcha_page_{page}.html")
                    break
                
                # Find all property listings - Zoopla's current structure
                listings = soup.find_all('div', {'data-testid': 'search-result'})
                
                if not listings:
                    # Try alternative class names if the above doesn't work
                    listings = soup.find_all('div', class_=lambda c: c and 'listing-results-wrapper' in c)
                    
                if not listings:
                    # Try another alternative
                    listings = soup.find_all('div', class_=lambda c: c and 'property-card' in c)
                
                if not listings:
                    print(f"No listings found on page {page}. Zoopla may have changed their HTML structure.")
                    # Save the HTML for debugging
                    with open(f"zoopla_debug_page_{page}.html", "w", encoding="utf-8") as f:
                        f.write(str(soup))
                    print(f"Saved HTML to zoopla_debug_page_{page}.html for debugging")
                    continue
                
                print(f"Found {len(listings)} listings on page {page}")
                
                # Process each listing
                for listing in listings:
                    property_data = {}
                    
                    # Extract price
                    price_elem = listing.find('p', {'data-testid': 'listing-price'})
                    if not price_elem:
                        price_elem = listing.find(class_=lambda c: c and ('price' in c.lower() if c else False))
                    if price_elem:
                        property_data['price'] = price_elem.text.strip()
                    
                    # Extract address
                    address_elem = listing.find('h2', {'data-testid': 'listing-title'})
                    if not address_elem:
                        address_elem = listing.find('h3', {'data-testid': 'listing-title'})
                    if not address_elem:
                        address_elem = listing.find(class_=lambda c: c and ('address' in c.lower() if c else False))
                    if address_elem:
                        property_data['address'] = address_elem.text.strip()
                    
                    # Extract details (beds, baths, etc.)
                    details_elem = listing.find('div', {'data-testid': 'listing-spec'})
                    if not details_elem:
                        details_elem = listing.find(class_=lambda c: c and ('specs' in c.lower() if c else False))
                    
                    if details_elem:
                        details_text = details_elem.text.strip()
                        
                        # Extract beds
                        beds_match = re.search(r'(\d+)\s*bed', details_text, re.IGNORECASE)
                        property_data['beds'] = beds_match.group(1) if beds_match else '0'
                        
                        # Extract baths
                        baths_match = re.search(r'(\d+)\s*bath', details_text, re.IGNORECASE)
                        property_data['baths'] = baths_match.group(1) if baths_match else '0'
                        
                        # Extract sq feet/area
                        area_match = re.search(r'(\d+,?\d*)\s*sq\s*ft', details_text, re.IGNORECASE)
                        if not area_match:
                            area_match = re.search(r'(\d+,?\d*)\s*m²', details_text, re.IGNORECASE)
                        property_data['sq_feet'] = area_match.group(1).replace(',', '') if area_match else '0'
                    
                    # Extract property type
                    type_elem = listing.find('p', {'data-testid': 'listing-description'})
                    if not type_elem:
                        type_elem = listing.find(class_=lambda c: c and ('description' in c.lower() if c else False))
                    
                    if type_elem:
                        type_text = type_elem.text.strip()
                        property_types = ['Detached', 'Semi-detached', 'Terraced', 'Flat', 'Bungalow', 'Apartment', 'House']
                        for p_type in property_types:
                            if p_type.lower() in type_text.lower():
                                property_data['type'] = p_type
                                break
                        else:
                            property_data['type'] = 'Not specified'
                    
                    # Extract link
                    link_elem = listing.find('a', {'data-testid': 'listing-details-link'})
                    if not link_elem:
                        link_elem = listing.find('a', href=lambda h: h and '/details/' in h)
                    
                    if link_elem and 'href' in link_elem.attrs:
                        href = link_elem['href']
                        if href.startswith('/'):
                            property_data['link'] = 'https://www.zoopla.co.uk' + href
                        else:
                            property_data['link'] = href
                    
                    if property_data:  # Only add if we found some data
                        all_properties.append(property_data)
                
                print(f"Successfully processed {len(all_properties)} properties from page {page}")
                
            except requests.exceptions.RequestException as e:
                print(f"Error fetching page {page}: {e}")
                continue
            except Exception as e:
                print(f"Unexpected error on page {page}: {e}")
                continue
    
    # Clean up data
    for prop in all_properties:
        if 'price' in prop:
            # Extract numeric price value
            price_text = prop['price']
            price_match = re.search(r'£?([\d,]+)', price_text)
            if price_match:
                prop['price'] = price_match.group(1).replace(',', '')
    
    return all_properties

def scrape_zoopla_api(location, num_pages=5):
    """Try to use Zoopla's API to get property data"""
    properties = []
    
    with requests.session() as s:
        # Set cookies and visit the homepage first
        s.get('https://www.zoopla.co.uk/', headers=headers)
        time.sleep(random.uniform(2, 4))
        
        for page in range(1, num_pages + 1):
            # Update headers with a random user agent for each request
            current_headers = headers.copy()
            current_headers['User-Agent'] = get_random_user_agent()
            current_headers['Content-Type'] = 'application/json'
            current_headers['Accept'] = 'application/json'
            
            # Try to find the API endpoint by examining the network requests
            api_url = f"https://www.zoopla.co.uk/api/v1/search?q={location}&page_size=25&page_number={page}&section=for-sale&view_type=list"
            
            try:
                time.sleep(random.uniform(5, 10))
                response = s.get(api_url, headers=current_headers)
                
                if response.status_code == 200 and 'application/json' in response.headers.get('Content-Type', ''):
                    data = response.json()
                    
                    # Save the API response for debugging
                    with open(f"zoopla_api_response_page_{page}.json", "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2)
                    
                    # Extract property data from the API response
                    # This will need to be adjusted based on the actual API response structure
                    if 'properties' in data:
                        for prop in data['properties']:
                            property_data = {}
                            
                            if 'price' in prop:
                                property_data['price'] = str(prop['price'])
                            
                            if 'address' in prop:
                                property_data['address'] = prop['address']
                            
                            if 'num_bedrooms' in prop:
                                property_data['beds'] = str(prop['num_bedrooms'])
                            
                            if 'num_bathrooms' in prop:
                                property_data['baths'] = str(prop['num_bathrooms'])
                            
                            if 'floor_area' in prop:
                                property_data['sq_feet'] = str(prop['floor_area'])
                            
                            if 'property_type' in prop:
                                property_data['type'] = prop['property_type']
                            
                            if 'details_url' in prop:
                                property_data['link'] = prop['details_url']
                            
                            properties.append(property_data)
                    
                    print(f"Successfully fetched {len(properties)} properties from API (page {page})")
                else:
                    print(f"API request failed with status code {response.status_code}")
                    return []
                
            except Exception as e:
                print(f"Error with API request: {e}")
                return []
    
    return properties

def save_to_csv(properties, filename):
    """Save properties to a CSV file"""
    if not properties:
        print("No properties to save")
        return
    
    # Get all possible fields from all properties
    fieldnames = set()
    for prop in properties:
        fieldnames.update(prop.keys())
    
    fieldnames = sorted(list(fieldnames))
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(properties)
    
    print(f"Saved {len(properties)} properties to {filename}")

def display_properties(properties, num=5):
    """Display the first few properties"""
    if not properties:
        print("No properties to display")
        return
    
    print("\nFirst few properties:")
    for i, prop in enumerate(properties[:num]):
        print(f"\nProperty {i+1}:")
        for key, value in prop.items():
            print(f"  {key}: {value}")

def print_alternative_options():
    print("\n===== ALTERNATIVE OPTIONS =====")
    print("Since direct scraping of Zoopla is blocked, consider these alternatives:")
    print("1. Use Zoopla's official API if available (requires registration)")
    print("2. Use a third-party real estate API like PropertyData or Rightmove")
    print("3. Use a web scraping service with proxy rotation like ScraperAPI or Bright Data")
    print("4. Consider using Rightmove or OnTheMarket which might be less restrictive")
    print("5. For educational purposes only, you could try using a VPN or proxy service")
    print("==============================\n")

if __name__ == "__main__":
    # Example usage
    location = input("Enter location to search (e.g., london): ").strip()
    if not location:
        location = "london"
    
    try:
        num_pages = int(input("Enter number of pages to scrape (default 5): ") or "5")
    except ValueError:
        num_pages = 5
    
    print(f"Scraping Zoopla for properties in {location}...")
    properties = scrape_zoopla(location, num_pages)
    
    if not properties:
        print("No properties found. Zoopla is likely blocking the scraper.")
        print_alternative_options()
    else:
        # Save to CSV
        output_file = f"zoopla_{location}_properties.csv"
        save_to_csv(properties, output_file)
        
        # Display first few properties
        display_properties(properties)
        
        # Also save as JSON for easier viewing
        with open(f"zoopla_{location}_properties.json", 'w', encoding='utf-8') as f:
            json.dump(properties, f, indent=2)