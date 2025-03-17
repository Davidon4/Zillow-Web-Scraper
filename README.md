# Zoopla Property Scraper

A Python script to scrape property listings from Zoopla.co.uk.

## Features

- Scrapes property listings from Zoopla search results
- Extracts property details including:
  - Price
  - Address
  - Number of bedrooms
  - Number of bathrooms
  - Square footage
  - Property type
  - Listing URL
- Saves results to a CSV file

## Requirements

- Python 3.6+
- Required packages (see requirements.txt)

## Installation

1. Clone this repository or download the files
2. Install the required packages:

```bash
pip install -r requirements.txt
```

## Usage

Run the script from the command line:

```bash
python Zoopla_Web_Scraper.py
```

You will be prompted to:
1. Enter a location to search (e.g., "london", "manchester", "birmingham")
2. Enter the number of pages to scrape (default is 5)

The script will:
- Scrape the specified number of pages
- Save the results to a CSV file named `zoopla_{location}_properties.csv`
- Display the first few properties found

## Notes

- The script includes random delays between requests to avoid being blocked
- If no listings are found, the HTML will be saved to a debug file for inspection
- The script attempts to handle different HTML structures that Zoopla might use

## Disclaimer

This script is for educational purposes only. Web scraping may be against the terms of service of some websites. Use responsibly and at your own risk. 