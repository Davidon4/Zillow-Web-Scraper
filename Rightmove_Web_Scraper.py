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
    'Referer': 'https://www.rightmove.co.uk/',
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

def scrape_rightmove(location, num_pages=5):
    """
    Scrape property listings from Rightmove
    
    Args:
        location (str): Location to search for properties
        num_pages (int): Number of pages to scrape
    
    Returns:
        list: List of dictionaries containing property data
    """
    all_properties = []
    
    # Define known location identifiers for common locations
    location_identifiers = {
        "london": "REGION%5E87490",
        "manchester": "REGION%5E162",
        "birmingham": "REGION%5E162",
        "leeds": "REGION%5E787",
        "liverpool": "REGION%5E138"
    }
    
    # Get the location identifier or use a default search approach
    location_lower = location.lower()
    location_id = location_identifiers.get(location_lower)
    
    with requests.session() as s:
        # First, visit the homepage to get cookies
        try:
            print("Setting up session...")
            s.get('https://www.rightmove.co.uk/', headers=headers, timeout=10)
            time.sleep(random.uniform(2, 4))
        except Exception as e:
            print(f"Error visiting homepage: {e}")
        
        # If we don't have a predefined location ID, try to get it
        if not location_id:
            try:
                print("Getting location identifier...")
                # Use the new URL format
                search_url = f"https://www.rightmove.co.uk/property-for-sale/search.html?searchLocation={quote(location)}&useLocationIdentifier=true"
                response = s.get(search_url, headers=headers, timeout=15)
                
                # Extract the location identifier from the response URL
                match = re.search(r'locationIdentifier=([^&]+)', response.url)
                if match:
                    location_id = match.group(1)
                    print(f"Found location identifier: {location_id}")
                else:
                    print("Could not find location identifier in URL")
                    # As a fallback, try a basic search with the location name
                    location_id = f"REGION%5E{location.lower()}"
                    print(f"Using fallback location identifier: {location_id}")
            except Exception as e:
                print(f"Error getting location identifier: {e}")
                # As a fallback, try a basic search with the location name
                location_id = f"REGION%5E{location.lower()}"
                print(f"Using fallback location identifier: {location_id}")
        else:
            print(f"Using predefined location identifier for {location}: {location_id}")
        
        for page in range(0, num_pages):
            try:
                # Add random delay between requests
                delay = random.uniform(3, 7)
                print(f"Waiting {delay:.2f} seconds before fetching page {page + 1}...")
                time.sleep(delay)
                
                # Update headers with random user agent
                current_headers = headers.copy()
                current_headers['User-Agent'] = get_random_user_agent()
                
                # Get the search results page - use the correct Rightmove URL format
                index = page * 24  # Rightmove shows 24 properties per page
                url = f"https://www.rightmove.co.uk/property-for-sale/find.html?searchType=SALE&locationIdentifier={location_id}&index={index}&propertyTypes=&includeSSTC=false&mustHave=&dontShow=&furnishTypes=&keywords="
                
                print(f"Fetching page {page + 1} with URL: {url}")
                response = s.get(url, headers=current_headers, timeout=15)
                
                if response.status_code != 200:
                    print(f"Error with status code: {response.status_code}")
                    # Try alternative URL format
                    url = f"https://www.rightmove.co.uk/property-for-sale/find.html?locationIdentifier={location_id}&index={index}"
                    print(f"Trying alternative URL: {url}")
                    response = s.get(url, headers=current_headers, timeout=15)
                
                response.raise_for_status()
                
                # Save the HTML for debugging
                with open(f"rightmove_page_{page + 1}.html", "w", encoding="utf-8") as f:
                    f.write(response.text)
                print(f"Saved HTML to rightmove_page_{page + 1}.html for debugging")
                
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
                for listing in listings:
                    property_data = {}
                    
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
                    
                    # Extract link
                    link_elem = listing.select_one('a.propertyCard-link, a.property-card-link, [data-test="property-details-link"]')
                    if not link_elem:
                        # Try to find any link that points to property details
                        link_elem = listing.find('a', href=lambda h: h and ('/properties/' in h or '/property-for-sale/' in h))
                    
                    if link_elem and 'href' in link_elem.attrs:
                        href = link_elem['href']
                        if href.startswith('/'):
                            property_data['link'] = 'https://www.rightmove.co.uk' + href
                        else:
                            property_data['link'] = href
                    
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
                
                if not page_properties:
                    print("No properties found on this page. Stopping search.")
                    break
                
            except requests.exceptions.RequestException as e:
                print(f"Error fetching page {page + 1}: {e}")
                continue
            except Exception as e:
                print(f"Unexpected error on page {page + 1}: {e}")
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

if __name__ == "__main__":
    # Example usage
    location = input("Enter location to search (e.g., London, Manchester, Birmingham): ").strip()
    if not location:
        location = "London"
    
    try:
        num_pages = int(input("Enter number of pages to scrape (default 5): ") or "5")
    except ValueError:
        num_pages = 5
    
    print(f"Scraping Rightmove for properties in {location}...")
    properties = scrape_rightmove(location, num_pages)
    
    if not properties:
        print("No properties found. Please check the location name or try again later.")
    else:
        # Save to CSV
        output_file = f"rightmove_{location.lower().replace(' ', '_')}_properties.csv"
        save_to_csv(properties, output_file)
        
        # Display first few properties
        display_properties(properties)
        
        # Also save as JSON for easier viewing
        json_file = f"rightmove_{location.lower().replace(' ', '_')}_properties.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(properties, f, indent=2)
        print(f"\nData also saved to {json_file}") 