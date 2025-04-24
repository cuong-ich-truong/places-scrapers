"""Places API scraper implementation."""

import time
from typing import Dict, Any, Tuple, List
import json
from google.protobuf.json_format import MessageToDict
from ..models.query import PlaceSearchQuery
from .google_places_api import GooglePlacesAPI


async def run_places_api_scraper(
    config: Dict[str, Any], output_file
) -> Tuple[float, List[float]]:
    """Run scraper using Places API."""
    api = GooglePlacesAPI()
    start_time = time.time()
    place_times = []
    default_location = "10.738727, 106.711703"  # Nguyễn Thị Thập, District 7, Ho Chi Minh City, Vietnam
    is_first_result = True

    for category in config["categories"]:
        category_start = time.time()
        print(f"\nProcessing category: {category}")

        # Create search query
        query = PlaceSearchQuery(
            textQuery=category + ", " + config["textQuery"],
            maxPlaces=config["maxPlaces"],
            location=config.get("location", default_location),
            radius=config["radiusKm"] * 1000,  # Convert km to meters
            polygon=config.get("polygon", None),
            languageCode=config.get("languageCode", "en"),
        )

        # Search for places
        search_start = time.time()
        response = await api.search_places(query)
        search_time = time.time() - search_start
        print(f"Search completed in {search_time:.2f} seconds")

        places = response.get("places", [])
        print(f"Found {len(places)} places")

        # Process places and add reviews
        for i, place_data in enumerate(places, 1):
            place_start = time.time()
            try:
                print(
                    f"\nProcessing place {i}/{len(places)}: {place_data.get('displayName', {}).get('text', 'Unknown')}"
                )

                # Add category to place data
                place_data["category"] = category

                # Get reviews if place has any
                if place_data.get("userRatingCount", 0) > 0:
                    print(
                        f"Getting reviews for place ID: {place_data.get('id', 'Unknown')}"
                    )
                    reviews_start = time.time()
                    reviews_data = await api.get_reviews(
                        place_data["id"], max_reviews=config.get("maxReviews", 100)
                    )
                    reviews_time = time.time() - reviews_start
                    print(
                        f"Fetched {len(reviews_data)} reviews in {reviews_time:.2f} seconds"
                    )

                    # Add reviews to place data
                    place_data["reviews"] = reviews_data

                # Convert any protobuf objects to dict before JSON serialization
                serializable_data = json.loads(json.dumps(place_data, default=str))

                # Write to file
                if not is_first_result:
                    output_file.write(",\n")
                json.dump(serializable_data, output_file, ensure_ascii=False, indent=4)
                is_first_result = False

                place_time = time.time() - place_start
                print(f"Place processed in {place_time:.2f} seconds")

            except Exception as e:
                print(f"Error processing place: {str(e)}")
                print(f"Problematic place data: {place_data}")
                continue

        category_time = time.time() - category_start
        place_times.append(category_time)
        print(f"\nCategory {category} completed in {category_time:.2f} seconds")
        print(f"Average time per place: {category_time/len(places):.2f} seconds")

    return start_time, place_times
