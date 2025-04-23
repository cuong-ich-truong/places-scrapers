# Places Scraper

**Places Scraper** is a Python-based tool designed to scrape location details and user reviews from Google Maps using **Selenium** and **BeautifulSoup**. This script allows you to gather data on nearby places, including their names, ratings, addresses, phone numbers, and reviews.

## Features

- Search for places by location and category
- Scrape place details (name, address, phone, rating)
- Collect reviews with ratings and dates
- Export results to JSON files
- Configurable search parameters

## Requirements

- Python 3.x
- Selenium
- BeautifulSoup4
- Chrome WebDriver

## Installation

1. Clone this repository
2. Install required packages:
```bash
pip install selenium beautifulsoup4
```
3. Install Chrome WebDriver that matches your Chrome browser version

## Configuration

Create a `config.json` file with the following structure:

```json
{
  "textQuery": "Đ. Nguyễn Thị Thập, District 7, Ho Chi Minh City, Vietnam",
  "radiusKm": 2,
  "categories": ["restaurant", "coffee"],
  "maxPlaces": 5,
  "maxReviews": 100,
  "scraper": "selenium",
  "output_dir": "output"
}
```

### Configuration Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| textQuery | string | Location to search for places | "Đ. Nguyễn Thị Thập, District 7, Ho Chi Minh City, Vietnam" |
| radiusKm | number | Search radius in kilometers | 2 |
| categories | array | List of place categories to search for | ["restaurant", "coffee"] |
| maxPlaces | number | Maximum number of places to scrape per category | 5 |
| maxReviews | number | Maximum number of reviews to collect per place | 100 |
| scraper | string | Scraper to use ("selenium" or "api") | "selenium" |
| output_dir | string | Directory to save output files | "output" |

## Usage

1. Update the `config.json` file with your desired search parameters
2. Create a `.env` file with the required environment variables (see `.env.example`)
3. Run the script:
```bash
# Using Selenium scraper (default)
python3 -m places_scraper

# Using Places API scraper 
python3 -m places_scraper
```

The script will automatically use the scraper specified in your `config.json` file (`scraper` field). No need to specify the method via command line arguments.

## Output

The script will:
1. Create the output directory specified in `config.json` (default: "output")
2. Generate a JSON file with timestamp in the filename (e.g., `20240321_143022.json`)
3. Save results in the following format:

```json
{
  "name": "Place Name",
  "address": "123 Street, City",
  "phone": "+1234567890",
  "website": "https://example.com",
  "rating": 4.5,
  "total_reviews": 100,
  "url": "https://maps.google.com/...",
  "category": "restaurant",
  "reviews": [
    {
      "author": "John Doe",
      "text": "Great place!",
      "rating": 5,
      "time": "2 weeks ago"
    }
  ]
}
```

## Notes

- The script uses Selenium to interact with Google Maps
- Results are saved incrementally to prevent data loss
- Progress and statistics are printed to the console
- The script handles errors gracefully and continues processing

## Limitations

### Selenium Approach

- **Performance**: The script takes approximately 3 seconds to scrape each place due to necessary delays for page loading and content rendering.
- **Review Collection**: A maximum of 10 reviews are collected per place to maintain reasonable execution time and prevent excessive data collection.
- **Rate Limiting**: The script includes built-in delays to avoid being blocked by Google Maps' rate limiting mechanisms.

### Places API Approach

- **Cost**: The Places APIs are free up to 10,000 requests per month. Exceeding this limit will incur charges.
- **Setup Overhead**: The Places API requires setting Google Project with Google Maps API service enabled and valid billing account.

## References

This project was inspired by and based on the work of [Ankush Rathour's GoogleMapsScraper](https://github.com/AnkushRathour/GoogleMapsScraper/tree/main). I have enhanced the original implementation with additional features and improvements.

## Contributing

We welcome contributions to Places Scraper! Feel free to fork the repository, create a branch, and submit a Pull Request with your improvements or new features.

## License
This project is licensed under the MIT License. See the LICENSE file for more information.

  
