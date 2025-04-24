"""Query models for API requests."""

from typing import TypedDict


class PlaceSearchQuery(TypedDict):
    """Query parameters for place search."""

    textQuery: str
    radius: int
    maxPlaces: int
    location: str
    languageCode: str
