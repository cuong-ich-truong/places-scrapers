"""Main entry point for the places scraper."""
import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from .utils.config import load_config, validate_config
from .utils.processor import process_places
from .scrapers.google_maps import get_places

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

def main():
    """Main function to run the scraper."""
    # Load and validate configuration
    config = load_config()
    validate_config(config)
    
    browser = webdriver.Chrome(options=CHROME_OPTIONS)

    # Create output directory if it doesn't exist
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
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

            for category in config['categories']:
                print(f"\nSearching for {category}...")
                places = get_places(
                    browser,
                    config,
                    category
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

    except Exception as error:
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