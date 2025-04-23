"""Models for place and review data."""

from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class Review:
    """Review data model."""

    author: str
    text: str
    rating: int
    time: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert review to dictionary."""
        return {
            "author": self.author,
            "text": self.text,
            "rating": self.rating,
            "time": self.time,
        }


@dataclass
class Place:
    """Place data model."""

    name: str
    address: str
    phone: str
    website: str
    rating: float
    total_reviews: int
    url: str
    category: str = ""
    reviews: List[Review] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert place to dictionary."""
        return {
            "name": self.name,
            "address": self.address,
            "phone": self.phone,
            "website": self.website,
            "rating": self.rating,
            "total_reviews": self.total_reviews,
            "url": self.url,
            "category": self.category,
            "reviews": [review.to_dict() for review in self.reviews],
        }
