# Imovelweb Scraper

This script scrapes data from the real estate website imovelweb.com.br. It specifically targets properties listed for sale in Belo Horizonte, Brazil. The script generates a csv file containing details about the properties and feeds the data into a Supabase database.

## Functionality

The script is built around the main function `scrap_buy(x, y=None, url_type="normal")`.

### Parameters:

- `x (int)`: First page to scrape. If `y` is not specified, this argument is treated as a single page input.
- `y (int, optional)`: Last page to scrape (not included in the range of pages to scrape). If specified, pages `x` to `y-1` will be scraped.
- `url_type (str, optional)`: Type of URL template to use. "normal" for normal URL or "last-day" for last day URL.

### Returns:

The function returns a csv file and feeds a database in Supabase.

## Requirements

To run the script, you need the following Python packages:

- selenium
- supabase
- numpy
- pandas
- re (regex)
- googlemaps
- time
- os
- unidecode
- dotenv
- rapidfuzz
- warnings

`pip install -r requirements.txt`

Additionally, you need to have valid API keys for Google Maps and Supabase, which should be stored as environment variables.

## Running the script

Simply import the function from the Python script and call it with your desired parameters.
