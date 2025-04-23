"""Hybrid scraper implementation using Places API and Selenium."""

import time
import json
from typing import Dict, Any, List, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
)

from .google_places_api import GooglePlacesAPI
from ..models.place import Place, Review
from ..utils.debug import debug


class HybridScraper:
    """Hybrid scraper using Places API for places and Selenium for reviews."""

    def __init__(self, options=None):
        """Initialize the hybrid scraper.

        Args:
            options: Optional Chrome options for Selenium
        """
        self.api = GooglePlacesAPI()
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 10)

    def close(self):
        """Close the browser."""
        if hasattr(self, "driver"):
            self.driver.quit()

    def __del__(self):
        """Cleanup when the object is destroyed."""
        self.close()

    def get_places(self, config: Dict[str, Any], category_name: str) -> List[Place]:
        """Get places using Places API.

        Args:
            config: Configuration dictionary
            category_name: Category to search for

        Returns:
            List of Place objects
        """
        # Create search query
        query = {
            "textQuery": category_name + ", " + config["textQuery"],
            "maxPlaces": config["maxPlaces"],
            "location": config.get(
                "location", "10.738727, 106.711703"
            ),  # Default to District 7
            "radius": config["radiusKm"] * 1000,  # Convert km to meters
            "polygon": config.get("polygon", None),
        }

        # Search for places
        response = self.api.search_places(query)
        places = response.get("places", [])

        # Convert API response to Place objects
        place_objects = []
        for place_data in places:
            place = Place(
                name=place_data.get("displayName", {}).get("text", ""),
                address=place_data.get("formattedAddress", ""),
                phone=place_data.get("nationalPhoneNumber", ""),
                website=place_data.get("websiteUri", ""),
                rating=place_data.get("rating", 0.0),
                total_reviews=place_data.get("userRatingCount", 0),
                url=f"https://www.google.com/maps/place/?q=place_id:{place_data['id']}",
                category=category_name,
            )
            place_objects.append(place)

        return place_objects

    def get_reviews(self, place_info: Place, max_reviews: int = 100) -> List[Review]:
        """Get reviews using Selenium.

        Args:
            place_info: Place object containing place information
            max_reviews: Maximum number of reviews to collect

        Returns:
            List of Review objects
        """
        reviews = []

        self.driver.get(place_info.url)
        time.sleep(1)  # Wait for page to load

        # Click on the "Reviews" tab
        try:
            reviews_button = self.wait.until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "button[aria-label*='Reviews for']")
                )
            )
            reviews_button.click()
        except (TimeoutException, ElementClickInterceptedException) as error:
            debug("get_reviews", error)
            return reviews

        # Scroll and collect reviews until we have enough or can't scroll anymore
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        max_scroll_attempts = 20
        processed_reviews = set()  # Track processed reviews to avoid duplicates

        while len(reviews) < max_reviews and scroll_attempts < max_scroll_attempts:
            try:
                # Wait for reviews to load
                self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.jftiEf"))
                )

                # Get current reviews
                review_divs = self.driver.find_elements(By.CSS_SELECTOR, "div.jftiEf")

                for review_div in review_divs:
                    if len(reviews) >= max_reviews:
                        break

                    try:
                        # Get review content
                        author = review_div.find_element(
                            By.CSS_SELECTOR, "div.d4r55"
                        ).text.strip()
                        date = review_div.find_element(
                            By.CSS_SELECTOR, "span.rsqaWe"
                        ).text.strip()
                        text = review_div.find_element(
                            By.CSS_SELECTOR, "span.wiI7pd"
                        ).text.strip()

                        # Create a unique key for this review
                        review_key = f"{author}_{date}_{text[:50]}"
                        if review_key in processed_reviews:
                            continue

                        # Get the rating
                        rating_element = review_div.find_element(
                            By.CSS_SELECTOR, "span.kvMYJc"
                        )
                        rating = (
                            rating_element.get_attribute("aria-label")
                            if rating_element
                            else ""
                        )
                        rating = rating.split()[0] if rating else "0"

                        # Create Review object
                        review = Review(
                            author=author, text=text, rating=int(rating), time=date
                        )
                        reviews.append(review)
                        processed_reviews.add(review_key)
                    except Exception as e:
                        debug("get_reviews", e)
                        continue

                # Scroll down
                self.driver.execute_script(
                    "window.scrollTo(0, document.body.scrollHeight);"
                )
                time.sleep(1)  # Wait for new content to load

                # Check if we've reached the end
                new_height = self.driver.execute_script(
                    "return document.body.scrollHeight"
                )
                if new_height == last_height:
                    break
                last_height = new_height
                scroll_attempts += 1

            except Exception as e:
                debug("get_reviews", e)
                break

        return reviews


def run_hybrid_scraper(
    config: Dict[str, Any], output_file
) -> Tuple[float, List[float]]:
    """Run the hybrid scraper.

    Args:
        config: Configuration dictionary
        output_file: File object to write results to
    """
    scraper = HybridScraper()
    start_time = time.time()
    place_times = []

    try:
        results = {}
        for category in config["categories"]:
            places = scraper.get_places(config, category)
            for place in places:
                place_start = time.time()
                print(f"Getting reviews for {place.name} ({place.url})")
                reviews = scraper.get_reviews(
                    place, max_reviews=config.get("maxReviews", 100)
                )
                place_time = time.time() - place_start
                place_times.append(place_time)
                # printout process time and number of reviews
                print(
                    f"Processed {len(reviews)} reviews for {place.name} in ({place_time:.2f} seconds)"
                )
                place.reviews = reviews
            results[category] = places

        # Save results
        for category, places in results.items():
            if category != config["categories"][0]:
                output_file.write(",\n")
            json.dump(
                [place.to_dict() for place in places],
                output_file,
                ensure_ascii=False,
            )
    finally:
        scraper.close()

    return start_time, place_times
