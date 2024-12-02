from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass
class Resource:
    """Represents a curated content resource.

    Args:
        id: Unique identifier for the resource
        title: Resource title
        url: Original resource URL
        categories: List of assigned categories
        ranking: Numerical quality ranking
        summary: Brief content summary
        full_content: Full content in markdown
        datetime: Creation/fetch timestamp
        source: Source URL of the content
    """

    id: str
    title: str
    url: str
    categories: List[str]
    ranking: float
    summary: str
    full_content: str
    datetime: datetime
    source: str
    removed: bool = False
    notes: str = ""
