from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import json
from datetime import datetime
import os

# Setup Selenium WebDriver
options = Options()
options.add_argument("--headless")
options.add_argument("window-size=1920,1080")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

def get_places(driver, search_term, radius_km, category, max_places):
  places = []
  search_query = f'{category} in {search_term}'
  url = f'https://www.google.com/maps/search/{search_query}/@{radius_km}z'
  
  print(f"\nSearch URL: {url}")

  driver.get(url)
  time.sleep(1)  # Reduced initial wait time

  # Find the results panel and scroll within it
  scroll_pause_time = 0.5  # Reduced pause time
  scroll_attempts = 0
  max_scroll_attempts = 10

  # Find the results panel
  results_panel = driver.find_element(By.CSS_SELECTOR, "div[role='feed']")
  
  while scroll_attempts < max_scroll_attempts and len(places) < max_places:
    # Scroll within the results panel
    driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", results_panel)
    time.sleep(scroll_pause_time)
    
    # Get current places
    page_content = driver.page_source
    soup = BeautifulSoup(page_content, "html.parser")
    data_elements = soup.find_all("div", class_="Nv2PK")
    
    # Update places list
    for element in data_elements[len(places):]:  # Only process new elements
      if len(places) >= max_places:
        break
      try:
        name = element.select_one('.qBF1Pd').text.strip() if element.select_one('.qBF1Pd') else ''
        rating = element.select_one('.MW4etd').text.strip() if element.select_one('.MW4etd') else ''
        link = element.select_one('a').get('href') if element.select_one('a') else ''

        # Get total reviews from the results list
        reviews_element = element.select_one('.UY7F9')
        total_reviews = 0
        if reviews_element:
          reviews_text = reviews_element.text.strip()
          # Extract number from text like "1,234 reviews"
          total_reviews = int(''.join(filter(str.isdigit, reviews_text)))

        places.append({
          'name': name,
          'address': '',
          'phone_number': '',
          'rating': rating,
          'link': link,
          'total_reviews': total_reviews
        })
      except Exception as e:
        continue
    
    if len(places) >= max_places:
      break
    
    scroll_attempts += 1
  
  print(f"Found {len(places)} places for {category}")
  return places

def get_reviews(driver, place):
  reviews = []

  driver.get(place['link'])
  time.sleep(1)  # Reduced initial wait time

  # Wait for the Reviews button to be present and clickable
  try:
    reviews_button = WebDriverWait(driver, 5).until(
      EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label*='Reviews for']"))
    )
    reviews_button.click()
  except Exception as e:
    print(f"Could not find or click Reviews button for {place['name']}: {str(e)}")
    return place, reviews

  page_content = driver.page_source
  soup = BeautifulSoup(page_content, "html.parser")

  # Get address and phone number
  address_element = soup.find("button", class_="CsEnBe", attrs={"data-item-id": "address"})
  phone_number_element = soup.find("button", class_="CsEnBe", attrs={"data-tooltip":"Copy phone number"})
  if address_element:
      place['address'] = address_element.get('aria-label') if address_element.get('aria-label') else ''
  if phone_number_element:
      place['phone_number'] = phone_number_element.get('aria-label') if phone_number_element.get('aria-label') else ''

  retry = 0
  while True:
    # retry till reviews element found
    page_content = driver.page_source
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
      author = review_div.find('div', class_='d4r55').text.strip() if review_div.find('div', class_='d4r55') else ''
      date = review_div.find('span', class_='rsqaWe').text.strip() if review_div.find('span', class_='rsqaWe') else ''
      text = review_div.find('span', class_='wiI7pd').text.strip() if review_div.find('span', class_='wiI7pd') else ''
      
      # Get the rating
      rating_element = review_div.find('span', class_='kvMYJc')
      rating = rating_element.get('aria-label') if rating_element else ''
      # Extract just the number from the rating (e.g., "5 stars" -> "5")
      rating = rating.split()[0] if rating else ''
      
      reviews.append({
        'author': author,
        'date': date,
        'text': text,
        'rating': rating
      })
    except Exception as e:
      continue

  # Add collected reviews count to place info
  place['collected_reviews'] = len(reviews)
  
  # Print review statistics
  

  return place, reviews

if __name__ == "__main__":
  # Load configuration from config.json
  config_path = os.path.join(os.path.dirname(__file__), 'config.json')
  with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)
  
  search_term = config['search_term']
  radius_km = config['radius_km']
  categories = config['categories']
  max_places = config['max_places']

  driver = webdriver.Chrome(options=options)

  # Create output directory if it doesn't exist
  output_dir = os.path.join(os.path.dirname(__file__), 'output')
  os.makedirs(output_dir, exist_ok=True)

  # Generate timestamp for filename
  timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
  filename = os.path.join(output_dir, f"{timestamp}.json")
  
  try:
    start_time = time.time()
    place_times = []
    first_result = True

    # Open the file once and keep it open
    with open(filename, 'w', encoding='utf-8') as f:
      f.write('[\n')

      for category in categories:
        print(f"\nSearching for {category}...")
        places = get_places(driver, search_term, radius_km, category, max_places)
        
        for i, place in enumerate(places, 1):
          try:
            place_start_time = time.time()
            place, reviews = get_reviews(driver, place)
            place_end_time = time.time()
            place_time = place_end_time - place_start_time
            place_times.append(place_time)
            
            result = {
              'place': place,
              'reviews': reviews,
              'category': category
            }

            # Write result to file
            if not first_result:
              f.write(',\n')
            json.dump(result, f, ensure_ascii=False)
            first_result = False
          
            print(f"Scraped place {i} of {len(places)} for {category}. Place: {place['name']} Reviews(scraped/total): {place['collected_reviews']}/{place['total_reviews']} ({place_time:.2f} secs)")
          except Exception as e:
            print(f"Error scraping place {i} for {category}: {str(e)}")
            continue

      # Close the JSON array
      f.write('\n]')

  except Exception as e:
    print(f"An error occurred during scraping: {str(e)}")
  finally:
    end_time = time.time()
    total_time = end_time - start_time
    avg_time_per_place = sum(place_times) / len(place_times) if place_times else 0

    print(f"\nStatistics:")
    print(f"Total places scraped: {len(place_times)}")
    print(f"Total runtime: {total_time:.2f} secs")
    print(f"Average time per place: {avg_time_per_place:.2f} secs")
    print(f"Results exported to: {filename}")

    driver.quit()
