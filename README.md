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
  "search_term": "Đ. Nguyễn Thị Thập, District 7, Ho Chi Minh City, Vietnam",
  "radius_km": 2,
  "categories": ["restaurant", "coffee"],
  "max_places": 5
}
```

### Configuration Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| search_term | string | Location to search for places | "Đ. Nguyễn Thị Thập, District 7, Ho Chi Minh City, Vietnam" |
| radius_km | number | Search radius in kilometers | 2 |
| categories | array | List of place categories to search for | ["restaurant", "coffee"] |
| max_places | number | Maximum number of places to scrape per category | 5 |

## Usage

1. Update the `config.json` file with your desired search parameters
2. Run the script:
```bash
python places_scraper.py
```

## Output

The script will:
1. Create an `output` directory if it doesn't exist
2. Generate a JSON file with timestamp in the filename (e.g., `20240321_143022.json`)
3. Save results in the following format:

```json
{
  "place": {
    "name": "Place Name",
    "address": "Full Address",
    "phone_number": "Phone Number",
    "rating": "4.5",
    "link": "Google Maps URL",
    "total_reviews": 1234,
    "collected_reviews": 10
  },
  "reviews": [
    {
      "author": "Reviewer Name",
      "date": "Review Date",
      "text": "Review Text",
      "rating": "5"
    }
  ],
  "category": "restaurant"
}
```

## Notes

- The script uses Selenium to interact with Google Maps
- Results are saved incrementally to prevent data loss
- Progress and statistics are printed to the console
- The script handles errors gracefully and continues processing

## Limitations

- **Performance**: The script takes approximately 3 seconds to scrape each place due to necessary delays for page loading and content rendering.
- **Review Collection**: A maximum of 10 reviews are collected per place to maintain reasonable execution time and prevent excessive data collection.
- **Rate Limiting**: The script includes built-in delays to avoid being blocked by Google Maps' rate limiting mechanisms.

## References

This project was inspired by and based on the work of [Ankush Rathour's GoogleMapsScraper](https://github.com/AnkushRathour/GoogleMapsScraper/tree/main). I have enhanced the original implementation with additional features and improvements.

## Contributing

We welcome contributions to Places Scraper! Feel free to fork the repository, create a branch, and submit a Pull Request with your improvements or new features.

## License
This project is licensed under the MIT License. See the LICENSE file for more information.

  
