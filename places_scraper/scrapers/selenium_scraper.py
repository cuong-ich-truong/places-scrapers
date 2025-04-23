"""Selenium scraper implementation."""

import time
from typing import Dict, Any, Tuple, List
import json

from .google_maps_scraper import GoogleMapsScraper
from ..models.place import Place, Review
from ..utils.debug import debug


def run_selenium_scraper(
    config: Dict[str, Any], output_file
) -> Tuple[float, List[float]]:
    """Run scraper using Selenium."""
    # Initialize Selenium scraper
    scraper = GoogleMapsScraper()
    start_time = time.time()
    place_times = []
    is_first_result = True

    try:
        for category in config["categories"]:
            print(f"\nSearching for {category}...")
            category_start = time.time()

            # Get places for the category
            places = scraper.get_places(config, category)

            # Process each place
            for place in places:
                place_start = time.time()
                try:
                    # Get reviews for the place
                    reviews = scraper.get_reviews(place)
                    place.reviews = reviews

                    # Write to file
                    if not is_first_result:
                        output_file.write(",\n")
                    json.dump(
                        place.to_dict(), output_file, ensure_ascii=False, indent=4
                    )
                    is_first_result = False

                    place_time = time.time() - place_start
                    place_times.append(place_time)
                    print(f"Place processed in {place_time:.2f} seconds")

                except Exception as e:
                    debug("run_selenium_scraper", e)
                    continue

            category_time = time.time() - category_start
            print(f"Category completed in {category_time:.2f} seconds")

    except Exception as e:
        print(f"Error in Selenium scraper: {str(e)}")
    finally:
        scraper.close()
        return start_time, place_times
