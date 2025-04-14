"""Data models for places and reviews."""
from typing import Dict, List, TypedDict

class Review(TypedDict):
    """Review data structure."""
    author: str
    date: str
    text: str
    rating: str

class Place(TypedDict):
    """Place data structure."""
    name: str
    address: str
    phone_number: str
    rating: str
    link: str
    total_reviews: int
    collected_reviews: int

class PlaceResult(TypedDict):
    """Complete place result including reviews."""
    place: Place
    reviews: List[Review]
    category: str 