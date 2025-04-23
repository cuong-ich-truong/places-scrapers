"""Google Maps scraping functionality."""

import time
from typing import Dict, List, Tuple, Any
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    TimeoutException,
    NoSuchElementException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from ..models.place import Place, Review
from ..utils.debug import debug


class GoogleMapsScraper:
    """Client for Google Maps scraping."""

    def __init__(self, options=None):
        """Initialize the Google Maps scraper.

        Args:
            options: Optional Chrome options
        """
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 10)

    def close(self):
        """Close the browser."""
        if hasattr(self, "driver"):
            self.driver.quit()

    def __del__(self):
        """Cleanup when the object is destroyed."""
        self.close()

    def extract_place_info(self, element: BeautifulSoup) -> Place:
        """Extract place information from a BeautifulSoup element.

        Args:
            element: BeautifulSoup element containing place information

        Returns:
            Dictionary containing extracted place information
        """
        name = (
            element.select_one(".qBF1Pd").text.strip()
            if element.select_one(".qBF1Pd")
            else ""
        )
        rating = (
            element.select_one(".MW4etd").text.strip()
            if element.select_one(".MW4etd")
            else ""
        )
        link = element.select_one("a").get("href") if element.select_one("a") else ""

        # Get total reviews from the results list
        reviews_element = element.select_one(".UY7F9")
        total_reviews = 0
        if reviews_element:
            reviews_text = reviews_element.text.strip()
            # Extract number from text like "1,234 reviews"
            total_reviews = int("".join(filter(str.isdigit, reviews_text)))

        place = Place(
            name=name,
            address="",
            rating=rating,
            url=link,
            total_reviews=total_reviews,
            phone="",
            website="",
        )
        return place

    def extract_review_info(self, review_div: BeautifulSoup) -> Review:
        """Extract review information from a BeautifulSoup element.

        Args:
            review_div: BeautifulSoup element containing review information

        Returns:
            Dictionary containing extracted review information
        """
        author = (
            review_div.find("div", class_="d4r55").text.strip()
            if review_div.find("div", class_="d4r55")
            else ""
        )
        date = (
            review_div.find("span", class_="rsqaWe").text.strip()
            if review_div.find("span", class_="rsqaWe")
            else ""
        )
        text = (
            review_div.find("span", class_="wiI7pd").text.strip()
            if review_div.find("span", class_="wiI7pd")
            else ""
        )

        # Get the rating
        rating_element = review_div.find("span", class_="kvMYJc")
        rating = rating_element.get("aria-label") if rating_element else ""
        # Extract just the number from the rating (e.g., "5 stars" -> "5")
        rating = rating.split()[0] if rating else ""

        review = Review(author=author, time=date, text=text, rating=rating)
        return review

    def get_places(self, config: Dict[str, Any], category_name: str) -> List[Place]:
        """Get places from Google Maps search results.

        Args:
            config: Configuration dictionary containing search parameters
            category_name: Type of places to search for

        Returns:
            List of dictionaries containing place information
        """
        places_list = []
        search_query = f'{category_name} in {config["textQuery"]}'
        url = (
            f'https://www.google.com/maps/search/{search_query}/@{config["radiusKm"]}z'
        )
        print(f"\nSearch URL: {url}")

        self.driver.get(url)
        time.sleep(1)  # Reduced initial wait time

        # Find the results panel and scroll within it
        scroll_pause_time = 0.5  # Reduced pause time
        scroll_attempts = 0
        max_scroll_attempts = 10

        # Find the results panel
        results_panel = self.driver.find_element(By.CSS_SELECTOR, "div[role='feed']")
        while (
            scroll_attempts < max_scroll_attempts
            and len(places_list) < config["maxPlaces"]
        ):
            # Scroll within the results panel
            self.driver.execute_script(
                "arguments[0].scrollTop = arguments[0].scrollHeight", results_panel
            )
            time.sleep(scroll_pause_time)

            # Get current places
            page_content = self.driver.page_source
            soup = BeautifulSoup(page_content, "html.parser")
            data_elements = soup.find_all("div", class_="Nv2PK")

            # Update places list
            for element in data_elements[
                len(places_list) :
            ]:  # Only process new elements
                if len(places_list) >= config["maxPlaces"]:
                    break
                try:
                    place_info = self.extract_place_info(element)
                    places_list.append(place_info)
                except (AttributeError, ValueError) as error:
                    print(f"Error processing place element: {error}")
                    continue

            if len(places_list) >= config["maxPlaces"]:
                break

            scroll_attempts += 1

        print(f"Found {len(places_list)} places for {category_name}")
        return places_list

    def get_reviews(self, place_info: Place, max_reviews: int = 100) -> List[Review]:
        """Get reviews for a specific place.

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

        # Get address and phone number
        try:
            address_element = self.wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "button[data-item-id='address']")
                )
            )
            place_info.address = address_element.get_attribute("aria-label") or ""
        except (TimeoutException, NoSuchElementException) as error:
            debug("get_reviews", error)
            place_info.address = ""

        try:
            phone_number_element = self.wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "button[data-tooltip='Copy phone number']")
                )
            )
            place_info.phone = phone_number_element.get_attribute("aria-label") or ""
        except (TimeoutException, NoSuchElementException) as error:
            debug("get_reviews", error)
            place_info.phone = ""

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
