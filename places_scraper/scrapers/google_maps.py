"""Google Maps scraping functionality."""
import time
from typing import Dict, List, Tuple, Any
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    TimeoutException
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from ..models.place import Place, Review

def extract_place_info(element: BeautifulSoup) -> Place:
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
        'total_reviews': total_reviews,
        'collected_reviews': 0
    }

def extract_review_info(review_div: BeautifulSoup) -> Review:
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

def get_places(
    browser: webdriver.Chrome,
    config: Dict[str, Any],
    category_name: str
) -> List[Place]:
    """Get places from Google Maps search results.
    
    Args:
        browser: Selenium WebDriver instance
        config: Configuration dictionary containing search parameters
        category_name: Type of places to search for
    
    Returns:
        List of dictionaries containing place information
    """
    places_list = []
    search_query = f'{category_name} in {config["search_term"]}'
    url = f'https://www.google.com/maps/search/{search_query}/@{config["radius_km"]}z'
    print(f"\nSearch URL: {url}")

    browser.get(url)
    time.sleep(1)  # Reduced initial wait time

    # Find the results panel and scroll within it
    scroll_pause_time = 0.5  # Reduced pause time
    scroll_attempts = 0
    max_scroll_attempts = 10

    # Find the results panel
    results_panel = browser.find_element(By.CSS_SELECTOR, "div[role='feed']")
    while scroll_attempts < max_scroll_attempts and len(places_list) < config["max_places"]:
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
            if len(places_list) >= config["max_places"]:
                break
            try:
                place_info = extract_place_info(element)
                places_list.append(place_info)
            except (AttributeError, ValueError) as error:
                print(f"Error processing place element: {error}")
                continue
        
        if len(places_list) >= config["max_places"]:
            break
        
        scroll_attempts += 1
    
    print(f"Found {len(places_list)} places for {category_name}")
    return places_list

def get_reviews(
    browser: webdriver.Chrome,
    place_info: Place
) -> Tuple[Place, List[Review]]:
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