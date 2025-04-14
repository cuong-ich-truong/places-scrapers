"""A script to scrape places and reviews from Google Maps."""

import json
import os
import time
from datetime import datetime
from typing import Dict, List, Tuple

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    TimeoutException
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Setup Selenium WebDriver
CHROME_OPTIONS = Options()
CHROME_OPTIONS.add_argument("--headless")
CHROME_OPTIONS.add_argument("window-size=1920,1080")
CHROME_OPTIONS.add_argument("--no-sandbox")
CHROME_OPTIONS.add_argument("--disable-dev-shm-usage")
CHROME_OPTIONS.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/91.0.4472.124 Safari/537.36"
)

def extract_place_info(element: BeautifulSoup) -> Dict[str, str]:
    """Extract place information from a BeautifulSoup element.

    Args:
        element: BeautifulSoup element containing place information

    Returns:
        Dictionary containing extracted place information
    """
    name = (
        element.select_one('.qBF1Pd').text.strip()
        if element.select_one('.qBF1Pd') else ''
    )
    rating = (
        element.select_one('.MW4etd').text.strip()
        if element.select_one('.MW4etd') else ''
    )
    link = (
        element.select_one('a').get('href')
        if element.select_one('a') else ''
    )

    # Get total reviews from the results list
    reviews_element = element.select_one('.UY7F9')
    total_reviews = 0
    if reviews_element:
        reviews_text = reviews_element.text.strip()
        # Extract number from text like "1,234 reviews"
        total_reviews = int(''.join(filter(str.isdigit, reviews_text)))

    return {
        'name': name,
        'address': '',
        'phone_number': '',
        'rating': rating,
        'link': link,
        'total_reviews': total_reviews
    }

def get_places(
    browser: webdriver.Chrome,
    location: str,
    radius: int,
    category_name: str,
    limit: int
) -> List[Dict[str, str]]:
    """Get places from Google Maps search results.
    
    Args:
        browser: Selenium WebDriver instance
        location: Location to search in
        radius: Search radius in kilometers
        category_name: Type of places to search for
        limit: Maximum number of places to collect
    
    Returns:
        List of dictionaries containing place information
    """
    places_list = []
    search_query = f'{category_name} in {location}'
    url = f'https://www.google.com/maps/search/{search_query}/@{radius}z'
    print(f"\nSearch URL: {url}")

    browser.get(url)
    time.sleep(1)  # Reduced initial wait time

    # Find the results panel and scroll within it
    scroll_pause_time = 0.5  # Reduced pause time
    scroll_attempts = 0
    max_scroll_attempts = 10

    # Find the results panel
    results_panel = browser.find_element(By.CSS_SELECTOR, "div[role='feed']")
    while scroll_attempts < max_scroll_attempts and len(places_list) < limit:
        # Scroll within the results panel
        browser.execute_script(
            "arguments[0].scrollTop = arguments[0].scrollHeight",
            results_panel
        )
        time.sleep(scroll_pause_time)
        
        # Get current places
        page_content = browser.page_source
        soup = BeautifulSoup(page_content, "html.parser")
        data_elements = soup.find_all("div", class_="Nv2PK")
        
        # Update places list
        for element in data_elements[len(places_list):]:  # Only process new elements
            if len(places_list) >= limit:
                break
            try:
                place_info = extract_place_info(element)
                places_list.append(place_info)
            except (AttributeError, ValueError) as error:
                print(f"Error processing place element: {error}")
                continue
        
        if len(places_list) >= limit:
            break
        
        scroll_attempts += 1
    
    print(f"Found {len(places_list)} places for {category_name}")
    return places_list

def extract_review_info(review_div: BeautifulSoup) -> Dict[str, str]:
    """Extract review information from a BeautifulSoup element.

    Args:
        review_div: BeautifulSoup element containing review information

    Returns:
        Dictionary containing extracted review information
    """
    author = (
        review_div.find('div', class_='d4r55').text.strip()
        if review_div.find('div', class_='d4r55') else ''
    )
    date = (
        review_div.find('span', class_='rsqaWe').text.strip()
        if review_div.find('span', class_='rsqaWe') else ''
    )
    text = (
        review_div.find('span', class_='wiI7pd').text.strip()
        if review_div.find('span', class_='wiI7pd') else ''
    )
    
    # Get the rating
    rating_element = review_div.find('span', class_='kvMYJc')
    rating = rating_element.get('aria-label') if rating_element else ''
    # Extract just the number from the rating (e.g., "5 stars" -> "5")
    rating = rating.split()[0] if rating else ''
    
    return {
        'author': author,
        'date': date,
        'text': text,
        'rating': rating
    }

def get_reviews(
    browser: webdriver.Chrome,
    place_info: Dict[str, str]
) -> Tuple[Dict[str, str], List[Dict[str, str]]]:
    """Get reviews for a specific place.
    
    Args:
        browser: Selenium WebDriver instance
        place_info: Dictionary containing place information
    
    Returns:
        Tuple of (updated place info, list of reviews)
    """
    reviews_list = []

    browser.get(place_info['link'])
    time.sleep(1)  # Reduced initial wait time

    # Wait for the Reviews button to be present and clickable
    try:
        reviews_button = WebDriverWait(browser, 5).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "button[aria-label*='Reviews for']")
            )
        )
        reviews_button.click()
    except (TimeoutException, ElementClickInterceptedException) as error:
        print(
            f"Could not find or click Reviews button for {place_info['name']}: "
            f"{str(error)}"
        )
        return place_info, reviews_list

    page_content = browser.page_source
    soup = BeautifulSoup(page_content, "html.parser")

    # Get address and phone number
    address_element = soup.find(
        "button", class_="CsEnBe", attrs={"data-item-id": "address"}
    )
    phone_number_element = soup.find(
        "button", class_="CsEnBe", attrs={"data-tooltip": "Copy phone number"}
    )
    if address_element:
        place_info['address'] = (
            address_element.get('aria-label')
            if address_element.get('aria-label') else ''
        )
    if phone_number_element:
        place_info['phone_number'] = (
            phone_number_element.get('aria-label')
            if phone_number_element.get('aria-label') else ''
        )

    retry = 0
    while True:
        # retry till reviews element found
        page_content = browser.page_source
        soup = BeautifulSoup(page_content, "html.parser")
        review_divs = soup.find_all("div", class_="jftiEf")
        if len(review_divs) > 0:
            break
        time.sleep(0.2)  # Reduced wait time

        retry += 1
        if retry > 10:  # Reduced max retries
            break

    for review_div in review_divs:
        try:
            review_info = extract_review_info(review_div)
            reviews_list.append(review_info)
        except (AttributeError, ValueError) as error:
            print(f"Error processing review: {error}")
            continue

    # Add collected reviews count to place info
    place_info['collected_reviews'] = len(reviews_list)
    return place_info, reviews_list

def process_places(
    browser: webdriver.Chrome,
    category: str,
    places: List[Dict[str, str]],
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
            
            result = {
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

def main():
    """Main function to run the scraper."""
    # Load configuration from config.json
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(config_path, 'r', encoding='utf-8') as config_file:
        config = json.load(config_file)
    
    search_location = config['search_term']
    search_radius = config['radius_km']
    search_categories = config['categories']
    max_places_per_category = config['max_places']

    browser = webdriver.Chrome(options=CHROME_OPTIONS)

    # Create output directory if it doesn't exist
    output_dir = os.path.join(os.path.dirname(__file__), 'output')
    os.makedirs(output_dir, exist_ok=True)

    # Generate timestamp for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file_path = os.path.join(output_dir, f"{timestamp}.json")
    
    start_time = time.time()
    place_times = []
    is_first_result = True

    try:
        # Open the file once and keep it open
        with open(output_file_path, 'w', encoding='utf-8') as output_file:
            output_file.write('[\n')

            for category in search_categories:
                print(f"\nSearching for {category}...")
                places = get_places(
                    browser,
                    search_location,
                    search_radius,
                    category,
                    max_places_per_category
                )
                
                is_first_result = process_places(
                    browser,
                    category,
                    places,
                    output_file,
                    is_first_result,
                    place_times
                )

            output_file.write('\n]')

    except (IOError, json.JSONDecodeError) as error:
        print(f"An error occurred: {str(error)}")
    finally:
        browser.quit()
        end_time = time.time()
        total_time = end_time - start_time
        avg_time_per_place = (
            sum(place_times) / len(place_times) if place_times else 0
        )

        print("\nScraping completed!")
        print(f"Total time: {total_time:.2f} seconds")
        print(f"Average time per place: {avg_time_per_place:.2f} seconds")
        print(f"Results saved to: {output_file_path}")

if __name__ == "__main__":
    main()
