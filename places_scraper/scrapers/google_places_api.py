"""Google Places API implementation."""

from typing import Dict, List, Any
from google.maps import places_v1
from dotenv import load_dotenv
import os
from ..models.query import PlaceSearchQuery
import time
from ..utils.debug import debug


class GooglePlacesAPI:
    """Client for Google Places API."""

    def __init__(self):
        """Initialize the Places API client."""
        # Load .env from the root directory
        env_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"
        )
        load_dotenv(env_path)

        self.api_key = os.getenv("PLACES_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Missing API credentials. Please set PLACES_API_KEY in .env file"
            )

        # Initialize the Places client
        self.client = places_v1.PlacesAsyncClient(
            client_options={"api_key": self.api_key}
        )

    async def search_places(self, query: PlaceSearchQuery) -> Dict[str, Any]:
        """Search for places using the Places API.

        Args:
            query: PlaceSearchQuery object containing search parameters

        Returns:
            Raw API response containing places data
        """
        radius_m = query.get("radiusKm", 0.5) * 1000
        location = query.get("location", None)
        location_bias = {
            "circle": {
                "center": {"latitude": location[1], "longitude": location[0]},
                "radius": radius_m,
            }
        }

        # Specify the fields to retrieve
        request = places_v1.SearchTextRequest(
            text_query=query["textQuery"],
            location_bias=location_bias,
            max_result_count=min(20, query["maxPlaces"]),
            language_code=query.get("languageCode", "en"),
        )

        field_mask = [
            "places.id",
            "places.display_name",
            "places.formatted_address",
            "places.location",
            "places.rating",
            "places.user_rating_count",
            "places.types",
        ]

        try:
            # Make the API call
            print("Making API call...")
            response = await self.client.search_text(
                request, metadata=[("x-goog-fieldmask", ",".join(field_mask))]
            )

            # Convert the response to the expected format
            places = []
            for place in response.places:
                place_data = {
                    "id": place.id,
                    "displayName": {
                        "text": str(place.display_name.text),
                        "languageCode": str(place.display_name.language_code),
                    },
                    "formattedAddress": place.formatted_address,
                    "location": {
                        "latitude": place.location.latitude,
                        "longitude": place.location.longitude,
                    },
                    "rating": place.rating if hasattr(place, "rating") else None,
                    "userRatingCount": (
                        place.user_rating_count
                        if hasattr(place, "user_rating_count")
                        else None
                    ),
                    "types": ", ".join(place.types) if hasattr(place, "types") else "",
                    "primaryType": (
                        place.primary_type if hasattr(place, "primary_type") else None
                    ),
                }
                places.append(place_data)

            return {
                "places": places,
                "nextPageToken": (
                    response.next_page_token
                    if hasattr(response, "next_page_token")
                    else None
                ),
            }

        except Exception as e:
            debug("search_places", e)
            return {"places": [], "nextPageToken": None}

    async def get_reviews(
        self, place_id: str, max_reviews: int = 100
    ) -> List[Dict[str, Any]]:
        """Get reviews for a place using its ID.

        Args:
            place_id: Google Places place_id
            max_reviews: Maximum number of reviews to fetch (default: 100)

        Returns:
            List of review data
        """
        all_reviews = []

        try:
            while len(all_reviews) < max_reviews:
                # Create the request
                request = places_v1.GetPlaceRequest(
                    name=f"places/{place_id}",
                )

                # Define the fields to retrieve
                field_mask = ["reviews"]

                print(f"Fetching reviews page {len(all_reviews) // 5 + 1}...")
                response = await self.client.get_place(
                    request, metadata=[("x-goog-fieldmask", ",".join(field_mask))]
                )

                # Process reviews
                reviews = response.reviews if hasattr(response, "reviews") else []
                for review in reviews:
                    review_data = {
                        "name": review.name,
                        "relative_publish_time_description": review.relative_publish_time_description,
                        "rating": review.rating,
                        "text": (
                            {
                                "text": str(review.text.text),
                                "language_code": str(review.text.language_code),
                            }
                            if hasattr(review, "text")
                            else None
                        ),
                        "original_text": (
                            {
                                "text": str(review.original_text.text),
                                "language_code": str(
                                    review.original_text.language_code
                                ),
                            }
                            if hasattr(review, "original_text")
                            else None
                        ),
                        "author_attribution": (
                            {
                                "display_name": str(
                                    review.author_attribution.display_name
                                ),
                                "uri": str(review.author_attribution.uri),
                                "photo_uri": str(review.author_attribution.photo_uri),
                            }
                            if hasattr(review, "author_attribution")
                            else None
                        ),
                        "publish_time": (
                            review.publish_time.isoformat()
                            if hasattr(review, "publish_time")
                            else None
                        ),
                    }
                    all_reviews.append(review_data)

                # Small delay before next request to avoid rate limiting
                time.sleep(1)

            print(f"Total reviews fetched: {len(all_reviews)}")
            return all_reviews

        except Exception as e:
            debug("get_reviews", e)
            return []
