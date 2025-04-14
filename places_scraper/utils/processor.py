"""Place processing and result writing functionality."""
import json
import time
from typing import List, Dict, Any

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException

from ..models.place import Place, Review, PlaceResult
from ..scrapers.google_maps import get_reviews

def process_places(
    browser: webdriver.Chrome,
    category: str,
    places: List[Place],
    output_file,
    is_first_result: bool,
    place_times: List[float]
) -> bool:
    """Process places for a category and write results to file.

    Args:
        browser: Selenium WebDriver instance
        category: Category being processed
        places: List of places to process
        output_file: File to write results to
        is_first_result: Whether this is the first result being written
        place_times: List to store processing times

    Returns:
        Updated is_first_result value
    """
    for i, place in enumerate(places, 1):
        try:
            place_start_time = time.time()
            place, reviews = get_reviews(browser, place)
            place_end_time = time.time()
            place_time = place_end_time - place_start_time
            place_times.append(place_time)
            
            result: PlaceResult = {
                'place': place,
                'reviews': reviews,
                'category': category
            }

            # Write the result to file
            if not is_first_result:
                output_file.write(',\n')
            json.dump(result, output_file, indent=4)
            is_first_result = False

            print(f"Processed {i}/{len(places)} places for {category}")
        except (NoSuchElementException, TimeoutException) as error:
            print(f"Error processing place: {str(error)}")
            continue
    
    return is_first_result 