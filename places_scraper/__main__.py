"""Main entry point for the places scraper."""

import os
import time
from datetime import datetime
import json
from typing import Dict, Any

from .utils.config import load_config, validate_config
from .scrapers.selenium_scraper import run_selenium_scraper
from .scrapers.places_api_scraper import run_places_api_scraper


def main():
    """Main entry point."""
    # Load and validate config
    config = load_config()
    validate_config(config)

    # Create output directory
    output_dir = config.get("output_dir", "output")
    os.makedirs(output_dir, exist_ok=True)

    # Create output file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = open(
        os.path.join(output_dir, f"places_{timestamp}.json"), "w", encoding="utf-8"
    )
    output_file.write("[\n")

    try:
        # Run appropriate scraper
        if config.get("scraper", "") == "selenium":
            start_time, place_times = run_selenium_scraper(config, output_file)
        else:
            start_time, place_times = run_places_api_scraper(config, output_file)

        # Write closing bracket
        output_file.write("\n]")

        # Print summary
        total_time = time.time() - start_time
        print(f"\nScraping completed in {total_time:.2f} seconds")
        print(
            f"Average time per category: {sum(place_times) / len(place_times):.2f} seconds"
        )

    except Exception as e:
        print(f"Error in main: {str(e)}")
    finally:
        output_file.close()


if __name__ == "__main__":
    main()
