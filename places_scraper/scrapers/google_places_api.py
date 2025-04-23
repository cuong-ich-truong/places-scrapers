"""Google Places API implementation."""
from typing import Dict, List, Any
import requests
from dotenv import load_dotenv
import os
from ..models.query import PlaceSearchQuery
import time

class GooglePlacesAPI:
    """Client for Google Places API."""
    
    def __init__(self):
        """Initialize the Places API client."""
        # Load .env from the root directory
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
        load_dotenv(env_path)
        
        self.api_key = os.getenv('PLACES_API_KEY')
        self.signing_secret = os.getenv('PLACES_SIGNING_SECRET')
        self.base_url = os.getenv('BASE_URL')
        
        if not self.api_key or not self.signing_secret:
            raise ValueError(
                "Missing API credentials. Please set PLACES_API_KEY and "
                "PLACES_SIGNING_SECRET in .env file"
            )
        
    def search_places(self, query: PlaceSearchQuery) -> Dict[str, Any]:
        """Search for places using the Places API.
        
        Args:
            query: PlaceSearchQuery object containing search parameters
            
        Returns:
            Raw API response containing places data
        """
        headers = {
            'Content-Type': 'application/json',
            'X-Goog-Api-Key': self.api_key,            
            'X-Goog-FieldMask': '*'
        }
        
        payload = {
            'textQuery': query['textQuery'],
            'pageSize': min(20, query['maxPlaces'])  # API max pageSize is 20
        }
        
        # Handle location bias based on what's provided in the query
        if 'polygon' in query and query['polygon']:
            # Convert polygon coordinates to the format expected by the API
            vertices = []
            for point in query['polygon']:
                vertices.append({
                    'latitude': point[1],  # Extract latitude by index
                    'longitude': point[0]  # Extract longitude by index
                })
            
            payload['locationBias'] = {
                'polygon': {
                    'vertices': vertices
                }
            }
        elif 'location' in query and query['location']:
            # Fallback to circle if polygon is not provided
            lat, lng = map(float, query['location'].split(','))
            payload['locationBias'] = {
                'circle': {
                    'center': {
                        'latitude': lat,
                        'longitude': lng
                    },
                    'radius': query['radius']
                }
            }
        
        all_results = []
        next_page_token = None
        
        try:
            while len(all_results) < query['maxPlaces']:
                # Add nextPageToken if we have one
                if next_page_token:
                    payload['pageToken'] = next_page_token
                
                print(f"Requesting places (page {len(all_results) // 20 + 1})...")
                response = requests.post(
                    f"{self.base_url}:searchText",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                
                data = response.json()
                
                # Add places from this page to results
                places = data.get('places', [])
                all_results.extend(places[:query['maxPlaces'] - len(all_results)])
                
                # Check if we have more pages
                next_page_token = data.get('nextPageToken')
                if not next_page_token or len(all_results) >= query['maxPlaces']:
                    break  # No more pages available or we have enough results
                
                # Small delay before next request to avoid rate limiting
                time.sleep(1)
            
            return {
                'places': all_results,
                'nextPageToken': next_page_token if len(all_results) < query['maxPlaces'] else None
            }
            
        except requests.exceptions.RequestException as e:
            print(f"Error searching places: {str(e)}")
            return {'places': [], 'nextPageToken': None}
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return {'places': [], 'nextPageToken': None}
        
    def get_reviews(self, place_id: str, max_reviews: int = 100) -> List[Dict[str, Any]]:
        """Get reviews for a place using its ID.
        
        Args:
            place_id: Google Places place_id
            max_reviews: Maximum number of reviews to fetch (default: 100)
            
        Returns:
            List of review data
        """
        headers = {
            'Content-Type': 'application/json',
            'X-Goog-Api-Key': self.api_key,
            'X-Goog-FieldMask': 'reviews'  # Get reviews and pagination token
        }
        
        all_reviews = []
        next_page_token = None
        
        try:
            while len(all_reviews) < max_reviews:
                # Add nextPageToken if we have one
                params = {'pageToken': next_page_token} if next_page_token else {}
                
                print(f"Fetching reviews page {len(all_reviews) // 5 + 1}...")
                response = requests.get(
                    f"{self.base_url}/{place_id}",
                    headers=headers,
                    params=params
                )
                response.raise_for_status()
                
                data = response.json()
                reviews = data.get('reviews', [])
                print(f"Found {len(reviews)} reviews in this page")
                
                # Add reviews up to max_reviews
                remaining = max_reviews - len(all_reviews)
                all_reviews.extend(reviews[:remaining])
                
                # Check if we have more pages and need more reviews
                next_page_token = data.get('nextPageToken')
                if not next_page_token or len(all_reviews) >= max_reviews:
                    break  # No more pages available or we have enough reviews
                
                # Small delay before next request to avoid rate limiting
                time.sleep(1)
            
            print(f"Total reviews fetched: {len(all_reviews)}")
            return all_reviews
            
        except requests.exceptions.RequestException as e:
            print(f"Error getting reviews: {str(e)}")
            return []
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return []
        