import os
import csv
import requests
from bs4 import BeautifulSoup
import re
import time
import random
import json
from urllib.parse import quote, urlencode

# More realistic browser headers
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-GB,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-Mode': 'navigate',
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
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:96.0) Gecko/20100101 Firefox/96.0'
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
    
    with requests.session() as s:
        # First, visit the homepage to get cookies
        try:
            print("Setting up session...")
            s.get('https://www.zoopla.co.uk/', headers=headers, timeout=10)
            time.sleep(random.uniform(2, 4))
        except Exception as e:
            print(f"Error visiting homepage: {e}")
        
        for page in range(1, num_pages + 1):
            try:
                # Add random delay between requests
                delay = random.uniform(3, 7)
                print(f"Waiting {delay:.2f} seconds before fetching page {page}...")
                time.sleep(delay)
                
                # Update headers with random user agent
                current_headers = headers.copy()
                current_headers['User-Agent'] = get_random_user_agent()
                
                # Construct the search URL for the current page
                if page == 1:
                    url = f"https://www.zoopla.co.uk/for-sale/property/{location.lower()}/?q={quote(location)}&search_source=home"
                else:
                    url = f"https://www.zoopla.co.uk/for-sale/property/{location.lower}/?q={quote(location)}&search_source=home&pn={page}"
                
                print(f"Fetching page {page} with URL: {url}")
                response = s.get(url, headers=current_headers, timeout=15)
                response.raise_for_status()
                
                # Save the HTML for debugging
                with open(f"zoopla_page_{page}.html", "w", encoding="utf-8") as f:
                    f.write(response.text)
                print(f"Saved HTML to zoopla_page_{page}.html for debugging")
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find all property listings - use multiple selectors to catch different HTML structures
                listings = []
                
                # Try different selectors that might match property listings
                selectors = [
                    '[data-testid="search-result"]',
                    '.listing-results-wrapper',
                    '.srp clearfix',
                    'article.listing-results'
                ]
                
                for selector in selectors:
                    listings = soup.select(selector)
                    if listings:
                        print(f"Found listings with selector: {selector}")
                        break
                
                if not listings:
                    print(f"No listings found on page {page}. The page structure might have changed.")
                    continue
                
                print(f"Found {len(listings)} listings on page {page}")
                
                # Process each listing
                page_properties = []
                for listing in listings:
                    property_data = {}
                    
                    # Extract price
                    price_elem = listing.select_one('[data-testid="listing-price"], .listing-results-price')
                    if price_elem:
                        property_data['price'] = price_elem.text.strip()
                    
                    # Extract address
                    address_elem = listing.select_one('[data-testid="listing-address"], .listing-results-address')
                    if address_elem:
                        property_data['address'] = address_elem.text.strip()
                    
                    # Extract property details (beds, baths, etc.)
                    details_elem = listing.select_one('[data-testid="listing-spec"], .listing-results-attributes')
                    if details_elem:
                        # Extract number of bedrooms
                        beds_elem = details_elem.find(string=re.compile(r'\d+\s*bed'))
                        if beds_elem:
                            beds_match = re.search(r'(\d+)\s*bed', beds_elem, re.IGNORECASE)
                            if beds_match:
                                property_data['beds'] = beds_match.group(1)
                        
                        # Extract number of bathrooms
                        baths_elem = details_elem.find(string=re.compile(r'\d+\s*bath'))
                        if baths_elem:
                            baths_match = re.search(r'(\d+)\s*bath', baths_elem, re.IGNORECASE)
                            if baths_match:
                                property_data['baths'] = baths_match.group(1)
                    
                    # Extract property type
                    type_elem = listing.select_one('[data-testid="listing-type"], .property-type')
                    if type_elem:
                        property_data['type'] = type_elem.text.strip()
                    
                    # Extract link
                    link_elem = listing.select_one('a[href*="/for-sale/details/"]')
                    if link_elem and 'href' in link_elem.attrs:
                        href = link_elem['href']
                        if href.startswith('/'):
                            property_data['link'] = 'https://www.zoopla.co.uk' + href
                        else:
                            property_data['link'] = href
                    
                    # Extract agent
                    agent_elem = listing.select_one('[data-testid="listing-agent"], .agent-results-link')
                    if agent_elem:
                        property_data['agent'] = agent_elem.text.strip()
                    
                    # Extract description
                    desc_elem = listing.select_one('[data-testid="listing-description"], .listing-results-description')
                    if desc_elem:
                        property_data['description'] = desc_elem.text.strip()
                    
                    if property_data:
                        page_properties.append(property_data)
                
                all_properties.extend(page_properties)
                print(f"Successfully processed {len(page_properties)} properties from page {page}")
                
                if not page_properties:
                    print("No properties found on this page. Stopping search.")
                    break
                
            except requests.exceptions.RequestException as e:
                print(f"Error fetching page {page}: {e}")
                continue
            except Exception as e:
                print(f"Unexpected error on page {page}: {e}")
                import traceback
                traceback.print_exc()
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
    location = input("Enter location to search (e.g., London, Manchester, Birmingham): ").strip()
    if not location:
        location = "London"
    
    try:
        num_pages = int(input("Enter number of pages to scrape (default 5): ") or "5")
    except ValueError:
        num_pages = 5
    
    print(f"Scraping Zoopla for properties in {location}...")
    properties = scrape_zoopla(location, num_pages)
    
    if not properties:
        print("No properties found. Please check the location name or try again later.")
    else:
        # Save to CSV
        output_file = f"zoopla_{location.lower().replace(' ', '_')}_properties.csv"
        save_to_csv(properties, output_file)
        
        # Display first few properties
        display_properties(properties)
        
        # Also save as JSON for easier viewing
        json_file = f"zoopla_{location.lower().replace(' ', '_')}_properties.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(properties, f, indent=2)
        print(f"\nData also saved to {json_file}")