"""
Pytest configuration and shared fixtures for AI Signal tests.

This file contains common test fixtures and pytest configuration
that can be used across all test modules.
"""

import asyncio
from datetime import datetime
from typing import List

import pytest

from aisignal.core.interfaces import OperationResult
from aisignal.core.models import Resource, UserContext

# ============================================================================
# Pytest Configuration
# ============================================================================


def pytest_configure(config):
    """Configure pytest with custom markers and settings"""
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "performance: marks tests as performance tests")
    config.addinivalue_line("markers", "slow: marks tests as slow running")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names"""
    for item in items:
        # Add integration marker to integration test files
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)

        # Add performance marker to performance tests
        if "performance" in item.name.lower() or "perf" in item.name.lower():
            item.add_marker(pytest.mark.performance)
            item.add_marker(pytest.mark.slow)

        # Add slow marker to tests that might take longer
        if any(
            keyword in item.name.lower()
            for keyword in ["large", "concurrent", "stress"]
        ):
            item.add_marker(pytest.mark.slow)


# ============================================================================
# Event Loop Configuration for Async Tests
# ============================================================================


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Service Container Fixtures
# ============================================================================


@pytest.fixture
def container():
    """Provide a test service container with mock services"""
    from tests.mocks import create_test_container

    return create_test_container()


@pytest.fixture
def empty_container():
    """Provide an empty service container for custom setup"""
    from aisignal.utils.advanced_service_container import ServiceContainer

    return ServiceContainer()


# ============================================================================
# User Context Fixtures
# ============================================================================


@pytest.fixture
def user_context():
    """Provide a standard test user context"""
    return UserContext(
        user_id="test_user",
    )


@pytest.fixture
def alternative_user_context():
    """Provide an alternative test user context for multi-user tests"""
    return UserContext(
        user_id="alternative_user",
    )


@pytest.fixture
def admin_user_context():
    """Provide an admin user context for privileged operations"""
    return UserContext(
        user_id="admin_user",
    )


# ============================================================================
# Core Service Fixtures
# ============================================================================


@pytest.fixture
def core_service(container):
    """Provide a mock core service"""
    from aisignal.core.interfaces import ICoreService

    return container.get(ICoreService)


@pytest.fixture
def storage_service(container):
    """Provide a mock storage service"""
    from aisignal.core.interfaces import IStorageService

    return container.get(IStorageService)


@pytest.fixture
def config_manager(container):
    """Provide a mock config manager"""
    from aisignal.core.interfaces import IConfigManager

    return container.get(IConfigManager)


@pytest.fixture
def content_service(container):
    """Provide a mock content service"""
    from aisignal.core.interfaces import IContentService

    return container.get(IContentService)


@pytest.fixture
def resource_manager(container):
    """Provide a mock resource manager"""
    from aisignal.core.interfaces import IResourceManager

    return container.get(IResourceManager)


# ============================================================================
# Test Data Fixtures
# ============================================================================


@pytest.fixture
def sample_resources(user_context) -> List[Resource]:
    """Provide sample resources for testing"""
    return [
        Resource(
            id="resource_1",
            user_id=user_context.user_id,
            title="AI and Machine Learning Fundamentals",
            url="https://example.com/ai-ml-fundamentals",
            categories=["AI", "Programming"],
            ranking=85.0,
            summary="A comprehensive guide to AI and machine learning concepts",
            full_content="# AI and ML Fundamentals\n\nThis is a detailed article...",
            datetime=datetime(2024, 1, 15, 10, 30, 0),
            source="https://example.com",
        ),
        Resource(
            id="resource_2",
            user_id=user_context.user_id,
            title="Advanced Python Programming Techniques",
            url="https://example.com/python-advanced",
            categories=["Programming"],
            ranking=65.0,
            summary="Advanced techniques for Python developers",
            full_content="# Advanced Python\n\nLearn advanced Python patterns...",
            datetime=datetime(2024, 1, 16, 14, 45, 0),
            source="https://example.com",
        ),
        Resource(
            id="resource_3",
            user_id=user_context.user_id,
            title="Data Science with Pandas",
            url="https://test.com/pandas-data-science",
            categories=["Data Science", "Programming"],
            ranking=75.0,
            summary="Using Pandas for data science workflows",
            full_content="# Data Science with Pandas\n\nPandas is essential...",
            datetime=datetime(2024, 1, 17, 9, 15, 0),
            source="https://test.com",
        ),
    ]


@pytest.fixture
def large_resource_dataset(user_context) -> List[Resource]:
    """Provide a large dataset of resources for performance testing"""
    resources = []
    categories_pool = ["AI", "Programming", "Data Science", "ML", "Web Dev", "DevOps"]
    sources_pool = [
        "https://example.com",
        "https://test.com",
        "https://blog.com",
        "https://tech.com",
        "https://dev.com",
    ]

    for i in range(100):
        resource = Resource(
            id=f"large_dataset_resource_{i}",
            user_id=user_context.user_id,
            title=f"Large Dataset Resource {i+1}",
            url=f"https://example.com/resource-{i+1}",
            categories=[categories_pool[i % len(categories_pool)]],
            ranking=30.0 + (i % 70),  # Rankings from 30 to 99
            summary=f"This is test resource number {i+1} for performance testing",
            full_content=f"# Resource {i+1}\n\nContent for resource {i+1}...",
            datetime=datetime(2024, 1, 1 + (i % 30), (i % 24), (i % 60), 0),
            source=sources_pool[i % len(sources_pool)],
        )
        resources.append(resource)

    return resources


@pytest.fixture
def multiuser_resources(user_context, alternative_user_context):
    """Provide resources for multiple users for isolation testing"""
    user1_resources = [
        Resource(
            id="user1_resource_1",
            user_id=user_context.user_id,
            title="User 1 - AI Research",
            url="https://user1.com/ai-research",
            categories=["AI", "Research"],
            ranking=80.0,
            summary="AI research by user 1",
            full_content="",
            datetime=datetime.now(),
            source="https://user1.com",
        ),
        Resource(
            id="user1_resource_2",
            user_id=user_context.user_id,
            title="User 1 - Python Tips",
            url="https://user1.com/python-tips",
            categories=["Programming"],
            ranking=70.0,
            summary="Python tips by user 1",
            full_content="",
            datetime=datetime.now(),
            source="https://user1.com",
        ),
    ]

    user2_resources = [
        Resource(
            id="user2_resource_1",
            user_id=alternative_user_context.user_id,
            title="User 2 - Data Analysis",
            url="https://user2.com/data-analysis",
            categories=["Data Science"],
            ranking=85.0,
            summary="Data analysis by user 2",
            full_content="",
            datetime=datetime.now(),
            source="https://user2.com",
        ),
        Resource(
            id="user2_resource_2",
            user_id=alternative_user_context.user_id,
            title="User 2 - Machine Learning",
            url="https://user2.com/machine-learning",
            categories=["ML", "AI"],
            ranking=75.0,
            summary="Machine learning by user 2",
            full_content="",
            datetime=datetime.now(),
            source="https://user2.com",
        ),
        Resource(
            id="user2_resource_3",
            user_id=alternative_user_context.user_id,
            title="User 2 - Deep Learning",
            url="https://user2.com/deep-learning",
            categories=["ML", "Deep Learning"],
            ranking=90.0,
            summary="Deep learning by user 2",
            full_content="",
            datetime=datetime.now(),
            source="https://user2.com",
        ),
    ]

    return {"user1_resources": user1_resources, "user2_resources": user2_resources}


# ============================================================================
# Configuration Fixtures
# ============================================================================


@pytest.fixture
def sample_config():
    """Provide sample configuration data for testing"""
    return {
        "categories": ["AI", "Programming", "Data Science", "Web Development"],
        "sources": [
            "https://example.com",
            "https://test.com",
            "https://blog.example.com",
        ],
        "api_keys": {"openai": "test-openai-key", "jinaai": "test-jina-key"},
        "min_threshold": 50.0,
        "max_threshold": 80.0,
        "obsidian": {"vault_path": "/test/vault", "template_path": "/test/template"},
        "prompts": {
            "content_extraction": "Extract the key information from this content",
            "categorization": "Categorize this content into relevant categories",
        },
    }


@pytest.fixture
def updated_config():
    """Provide updated configuration for testing config updates"""
    return {
        "categories": ["Machine Learning", "DevOps", "Cloud Computing"],
        "sources": ["https://newsite.com"],
        "min_threshold": 60.0,
        "max_threshold": 85.0,
    }


# ============================================================================
# Mock Data Fixtures
# ============================================================================


@pytest.fixture
def mock_source_content():
    """Provide mock content from various sources"""
    return {
        "https://example.com": """
# Example Article
This is a comprehensive article about artificial intelligence and machine learning.

## Key Points
- AI is transforming industries
- Machine learning requires quality data
- Ethics in AI is crucial

## Conclusion
The future of AI looks promising with proper implementation.
        """,
        "https://test.com": """
# Programming Best Practices
Guidelines for writing clean, maintainable code.

## Principles
1. Write readable code
2. Follow consistent style
3. Add meaningful comments
4. Test your code

## Tools
- Linters
- Formatters
- Testing frameworks
        """,
        "https://blog.com": """
# Data Science Workflow
A complete guide to data science project lifecycle.

## Steps
1. Problem definition
2. Data collection
3. Data cleaning
4. Analysis
5. Model building
6. Deployment

## Best Practices
- Document everything
- Version control
- Reproducible research
        """,
    }


@pytest.fixture
def mock_api_responses():
    """Provide mock API responses for external services"""
    return {
        "jina_ai_response": {
            "content": "Extracted content from Jina AI",
            "metadata": {
                "title": "Test Article",
                "description": "A test article for Jina AI",
            },
        },
        "openai_analysis": {
            "categories": ["AI", "Programming"],
            "ranking": 75.0,
            "summary": "This is an AI-generated summary of the content",
        },
    }


# ============================================================================
# Async Test Utilities
# ============================================================================


@pytest.fixture
async def async_test_timeout():
    """Provide timeout for async tests"""
    return 30.0  # 30 seconds default timeout


@pytest.fixture
def async_test_runner():
    """Provide utility for running async tests"""

    class AsyncTestRunner:
        @staticmethod
        async def run_with_timeout(coro, timeout=30.0):
            """Run coroutine with timeout"""
            return await asyncio.wait_for(coro, timeout=timeout)

        @staticmethod
        async def run_concurrent(coros, return_when=asyncio.ALL_COMPLETED):
            """Run multiple coroutines concurrently"""
            if not coros:
                return []
            return await asyncio.gather(*coros, return_exceptions=True)

    return AsyncTestRunner()


# ============================================================================
# Performance Testing Utilities
# ============================================================================


@pytest.fixture
def performance_monitor():
    """Provide performance monitoring utilities"""
    import time
    from contextlib import contextmanager

    class PerformanceMonitor:
        def __init__(self):
            self.measurements = {}

        @contextmanager
        def measure(self, operation_name):
            """Context manager to measure operation time"""
            start_time = time.time()
            try:
                yield
            finally:
                end_time = time.time()
                self.measurements[operation_name] = end_time - start_time

        def get_measurement(self, operation_name):
            """Get measurement for an operation"""
            return self.measurements.get(operation_name)

        def assert_performance(self, operation_name, max_seconds):
            """Assert that operation completed within time limit"""
            actual_time = self.measurements.get(operation_name)
            assert actual_time is not None, f"No measurement for {operation_name}"
            assert actual_time <= max_seconds, (
                f"Operation {operation_name} took {actual_time:.3f}s, "
                f"expected <= {max_seconds}s"
            )

        def clear(self):
            """Clear all measurements"""
            self.measurements.clear()

    return PerformanceMonitor()


# ============================================================================
# Test Helper Utilities
# ============================================================================


@pytest.fixture
def test_helpers():
    """Provide test helper utilities"""

    class TestHelpers:
        @staticmethod
        def assert_operation_success(result: OperationResult, message: str = ""):
            """Assert that an operation was successful"""
            assert result.is_success, f"Operation failed: {result.message}. {message}"

        @staticmethod
        def assert_operation_failure(
            result: OperationResult, expected_error: str = None
        ):
            """Assert that an operation failed"""
            assert result.is_error, "Expected operation to fail"
            if expected_error:
                assert (
                    expected_error.lower() in result.message.lower()
                ), f"Expected error '{expected_error}' not found in '{result.message}'"

        @staticmethod
        def assert_resources_equal(
            resource1: Resource, resource2: Resource, ignore_fields=None
        ):
            """Assert that two resources are equal, optionally ignoring some fields"""
            ignore_fields = ignore_fields or []

            for field in [
                "id",
                "user_id",
                "title",
                "url",
                "categories",
                "ranking",
                "summary",
            ]:
                if field not in ignore_fields:
                    assert getattr(resource1, field) == getattr(resource2, field), (
                        f"Field {field} differs: {getattr(resource1, field)} "
                        f"!= {getattr(resource2, field)}"
                    )

        @staticmethod
        def create_test_resource(
            user_id: str, resource_id: str = None, **kwargs
        ) -> Resource:
            """Create a test resource with default values"""
            defaults = {
                "id": resource_id or f"test_resource_{hash(user_id) % 1000}",
                "user_id": user_id,
                "title": "Test Resource",
                "url": "https://test.example.com/resource",
                "categories": ["Test"],
                "ranking": 70.0,
                "summary": "A test resource for testing purposes",
                "full_content": "# Test Resource\n\nThis is test content.",
                "datetime": datetime.now(),
                "source": "https://test.example.com",
            }
            defaults.update(kwargs)
            return Resource(**defaults)

    return TestHelpers()


# ============================================================================
# Database and Storage Fixtures
# ============================================================================


@pytest.fixture
def temp_storage_path(tmp_path):
    """Provide a temporary path for storage testing"""
    storage_dir = tmp_path / "test_storage"
    storage_dir.mkdir()
    return storage_dir


@pytest.fixture
def test_database_url(temp_storage_path):
    """Provide a test database URL"""
    return f"sqlite:///{temp_storage_path}/test.db"


# ============================================================================
# Cleanup Fixtures
# ============================================================================


@pytest.fixture
def cleanup_tracker():
    """Track resources that need cleanup after tests"""
    cleanup_items = []

    def add_cleanup(item_type, item_id, cleanup_func=None):
        """Add an item to be cleaned up"""
        cleanup_items.append((item_type, item_id, cleanup_func))

    yield add_cleanup

    # Cleanup after test
    for item_type, item_id, cleanup_func in cleanup_items:
        if cleanup_func:
            try:
                if asyncio.iscoroutinefunction(cleanup_func):
                    asyncio.run(cleanup_func(item_id))
                else:
                    cleanup_func(item_id)
            except Exception as e:
                print(f"Warning: Failed to cleanup {item_type} {item_id}: {e}")


# ============================================================================
# Pytest Marks and Parameterization Helpers
# ============================================================================

# Common test parameters
SERVICE_SCOPES = pytest.mark.parametrize("scope", ["singleton", "transient", "scoped"])

RESOURCE_FILTERS = pytest.mark.parametrize(
    "filter_type,filter_value",
    [
        ("categories", ["AI"]),
        ("sources", ["https://example.com"]),
        ("categories", ["Programming", "AI"]),
    ],
)

PAGINATION_PARAMS = pytest.mark.parametrize(
    "limit,offset,expected_count",
    [
        (10, 0, 10),
        (5, 5, 5),
        (20, 0, 20),
        (None, 0, None),  # No limit
    ],
)


# ============================================================================
# Test Environment Configuration
# ============================================================================


@pytest.fixture(scope="session", autouse=True)
def test_environment_setup():
    """Set up test environment configuration"""
    import logging
    import os

    # Set test environment variables
    os.environ["TESTING"] = "true"
    os.environ["LOG_LEVEL"] = "DEBUG"

    # Configure logging for tests
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Suppress verbose logs from external libraries during testing
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    yield

    # Cleanup after all tests
    if "TESTING" in os.environ:
        del os.environ["TESTING"]
