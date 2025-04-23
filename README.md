# Places Scraper

A Python tool for scraping place information and reviews from Google Maps using different methods.

## Features

- Multiple scraping methods:
  - Selenium: Full browser automation for places and reviews
  - Places API: Fast and reliable place information retrieval
  - Hybrid: Combines Places API for places and Selenium for reviews
- Configurable search parameters

## Requirements

Please refer to the requirements.txt file for the list of dependencies.

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/places-scraper.git
cd places-scraper
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file in the project root with the variables listed in the .env.example file.

## Configuration

Create a `config.json` file with the following structure:

```json
{
    "scraper": "hybrid",  // Options: "selenium", "api", or "hybrid"
    "categories": [
        "restaurants",
        "cafes",
        "hotels"
    ],
    "textQuery": "in District 7, Ho Chi Minh City",
    "maxPlaces": 20,
    "radiusKm": 2,
    "location": "10.738727, 106.711703",
    "maxReviews": 100,
    "output_dir": "output"
}
```

### Configuration Parameters

- `scraper`: Choose the scraping method
  - `selenium`: Uses browser automation for both places and reviews
  - `api`: Uses Google Places API for places (no reviews)
  - `hybrid`: Uses Places API for places and Selenium for reviews (recommended)
- `categories`: List of categories to search for
- `textQuery`: Additional search terms
- `maxPlaces`: Maximum number of places to fetch per category
- `radiusKm`: Search radius in kilometers
- `location`: Center point for the search (latitude, longitude)
- `maxReviews`: Maximum number of reviews to fetch per place
- `output_dir`: Directory to save output files

## Usage

Run the scraper:
```bash
python -m places_scraper
```

The script will:
1. Load configuration from `config.json`
2. Create the output directory if it doesn't exist
3. Run the selected scraper
4. Save results to JSON files in the output directory

## Output

Results are saved in the output directory with timestamps:
```
output/
  places_20240315_123456.json
```

Each place entry includes:
- Basic information (name, address, phone, website)
- Rating and total reviews
- Individual reviews with text and ratings

## Scraper Comparison

| Feature           | Selenium | Places API | Hybrid |
|------------------|----------|------------|--------|
| Place Info       | ✓        | ✓          | ✓      |
| Reviews          | ✓        | ✗          | ✓      |
| Speed            | Slow     | Fast       | Medium |
| Reliability      | Medium   | High       | High   |
| API Quota Usage  | None     | High       | Low    |

## Troubleshooting

1. **Selenium Issues**:
   - Ensure Chrome is installed
   - Check Chrome version matches webdriver
   - Try increasing wait times in config

2. **API Issues**:
   - Verify API key is valid
   - Check API quota limits
   - Ensure location parameters are correct
   - Limit number of reviews to 5 per place

3. **General Issues**:
   - Check internet connection
   - Verify configuration file format
   - Look for error messages in console

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Credits

- This project was inspired by and based on the work of [Ankush Rathour's GoogleMapsScraper](https://github.com/AnkushRathour/GoogleMapsScraper/tree/main). I have enhanced the original implementation with additional features and improvements.