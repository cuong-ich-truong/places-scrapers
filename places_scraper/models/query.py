"""Query models for API requests."""
from typing import TypedDict

class PlaceSearchQuery(TypedDict):
    """Query parameters for place search."""
    field_masks: str
    textQuery: str
    radius: int
    maxPlaces: int
    location: str
    polygon: list[list[float]]