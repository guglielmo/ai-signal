from datetime import datetime

import pytest

from aisignal.core.models import Resource


def test_resource_creation():
    """Test Resource dataclass creation."""
    resource = Resource(
        id="1",
        title="Test",
        url="https://test.com",
        categories=["AI/ML"],
        ranking=0.8,
        summary="Test summary",
        full_content="Test content",
        datetime=datetime.now(),
        source="https://source.com",
    )
    assert resource.id == "1"
    assert resource.title == "Test"
    assert "AI/ML" in resource.categories
