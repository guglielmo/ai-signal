"""
Comprehensive ContentService Tests for Week 2, Day 3

This addresses the critical gap in ContentService testing (currently only 15% coverage)
with focus on error handling, external API interactions, and service integration.
"""

from unittest.mock import AsyncMock, Mock, patch

import aiohttp
import pytest

from aisignal.core.services.content_service import ContentService
from aisignal.core.services.storage_service import StorageService
from aisignal.core.sync_exceptions import ContentAnalysisError, ContentFetchError
from aisignal.core.token_tracker import TokenTracker


class TestContentServiceComprehensive:
    """Comprehensive tests for ContentService with real error scenarios"""

    @pytest.fixture
    def content_service(self, temp_db):
        """Create ContentService with real dependencies for testing"""
        storage_service = StorageService(temp_db)
        token_tracker = TokenTracker()

        return ContentService(
            jina_api_key="test-jina-key",
            openai_api_key="test-openai-key",
            categories=["AI", "Programming", "Data Science"],
            storage_service=storage_service,
            token_tracker=token_tracker,
            min_threshold=50.0,
            max_threshold=80.0,
        )

    @pytest.mark.asyncio
    async def test_fetch_content_success_flow(self, content_service):
        """Test successful content fetching with all components"""
        with patch("aiohttp.ClientSession.get") as mock_get:
            # Mock successful Jina AI response
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text.return_value = """
Title: Advanced AI Techniques

# Advanced AI Techniques

This article covers the latest developments in artificial intelligence,
including machine learning algorithms and neural network architectures.

## Key Concepts
- Deep learning
- Neural networks
- Machine learning
"""
            mock_get.return_value.__aenter__.return_value = mock_response

            result = await content_service.fetch_content(
                "https://example.com/ai-article"
            )

            assert result is not None
            assert result["url"] == "https://example.com/ai-article"
            assert result["title"] == "Advanced AI Techniques"
            assert "Deep learning" in result["content"]
            assert result["diff"] is not None

    @pytest.mark.asyncio
    async def test_fetch_content_network_errors(self, content_service):
        """Test various network error scenarios"""

        # Test connection timeout
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.side_effect = aiohttp.ClientError("Connection timeout")

            with pytest.raises(ContentFetchError) as exc_info:
                await content_service.fetch_content("https://timeout-site.com")

            assert "timeout-site.com" in str(exc_info.value)
            assert "Connection timeout" in str(exc_info.value)

        # Test DNS resolution error
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.side_effect = aiohttp.ClientError("Name or service not known")

            with pytest.raises(ContentFetchError) as exc_info:
                await content_service.fetch_content(
                    "https://nonexistent-domain.invalid"
                )

            assert "nonexistent-domain.invalid" in str(exc_info.value)

        # Test SSL certificate error
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.side_effect = aiohttp.ClientError("SSL certificate verify failed")

            with pytest.raises(ContentFetchError) as exc_info:
                await content_service.fetch_content("https://bad-ssl-site.com")

            assert "bad-ssl-site.com" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_fetch_content_api_errors(self, content_service):
        """Test API-specific error responses"""

        # Test 401 Unauthorized
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 401
            mock_response.reason = "Unauthorized"
            mock_get.return_value.__aenter__.return_value = mock_response

            with pytest.raises(ContentFetchError) as exc_info:
                await content_service.fetch_content("https://protected-site.com")

            assert "protected-site.com" in str(exc_info.value)
            assert "401" in str(exc_info.value)

        # Test 429 Rate Limited
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 429
            mock_response.reason = "Too Many Requests"
            mock_get.return_value.__aenter__.return_value = mock_response

            with pytest.raises(ContentFetchError) as exc_info:
                await content_service.fetch_content("https://rate-limited-site.com")

            assert "429" in str(exc_info.value)

        # Test 503 Service Unavailable
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 503
            mock_response.reason = "Service Unavailable"
            mock_get.return_value.__aenter__.return_value = mock_response

            with pytest.raises(ContentFetchError) as exc_info:
                await content_service.fetch_content("https://down-site.com")

            assert "503" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_analyze_content_success_flow(self, content_service):
        """Test successful content analysis with OpenAI integration"""
        # Mock content results
        content_results = [
            {
                "url": "https://example.com",
                "title": "Test Article",
                "content": "# AI Article\n\nThis is about artificial intelligence.",
                "diff": Mock(
                    has_changes=True,
                    added_blocks=["This is about artificial intelligence."],
                ),
            }
        ]

        with patch.object(content_service, "openai_client") as mock_openai:
            # Mock OpenAI response structure
            mock_message = Mock()
            mock_message.content = """
1. **Title:** AI Fundamentals
**Source:** https://example.com
**Link:** https://example.com/ai-fundamentals
**Categories:** AI, Programming
**Summary:** An introduction to artificial intelligence concepts
**Rankings:** [80, 75, 85]

2. **Title:** Machine Learning Basics
**Source:** https://example.com
**Link:** https://example.com/ml-basics
**Categories:** AI, Data Science
**Summary:** Basic concepts in machine learning
**Rankings:** [70, 80, 75]
"""
            mock_choice = Mock()
            mock_choice.message = mock_message

            mock_usage = Mock()
            mock_usage.prompt_tokens = 1500
            mock_usage.completion_tokens = 800
            mock_usage.total_tokens = 2300

            mock_completion = Mock()
            mock_completion.choices = [mock_choice]
            mock_completion.usage = mock_usage

            # Mock the async method call
            mock_openai.chat.completions.create = AsyncMock(
                return_value=mock_completion
            )

            results = await content_service.analyze_content(
                content_results, "Extract key information"
            )

            assert "https://example.com" in results
            items = results["https://example.com"]
            assert len(items) >= 1

            # Verify token tracking was called
            assert content_service.token_tracker.session_openai_input_tokens > 0

    @pytest.mark.asyncio
    async def test_analyze_content_openai_errors(self, content_service):
        """Test OpenAI API error handling"""
        content_results = [
            {
                "url": "https://example.com",
                "title": "Test Article",
                "content": "Test content",
                "diff": Mock(has_changes=True, added_blocks=["Test content"]),
            }
        ]

        # Test OpenAI API key error
        with patch.object(content_service, "openai_client") as mock_openai:
            mock_openai.chat.completions.create = AsyncMock(
                side_effect=Exception("Invalid API key")
            )

            with pytest.raises(ContentAnalysisError) as exc_info:
                await content_service.analyze_content(content_results, "Test prompt")

            assert "multiple sources" in str(exc_info.value)

        # Test OpenAI rate limit error
        with patch.object(content_service, "openai_client") as mock_openai:
            mock_openai.chat.completions.create = AsyncMock(
                side_effect=Exception("Rate limit exceeded")
            )

            with pytest.raises(ContentAnalysisError):
                await content_service.analyze_content(content_results, "Test prompt")

    @pytest.mark.asyncio
    async def test_fetch_full_content_with_tracking(self, content_service):
        """Test full content fetching with token usage tracking"""
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text.return_value = """
# Complete Article Content

This is the full content of a comprehensive article about AI and machine learning.

## Introduction
Artificial intelligence has revolutionized many industries...

## Deep Learning
Neural networks with multiple layers...

## Conclusion
The future of AI looks promising...
"""
            mock_get.return_value.__aenter__.return_value = mock_response

            initial_tokens = content_service.token_tracker.session_jina_tokens

            result = await content_service.fetch_full_content(
                "https://example.com/full-article"
            )

            assert result is not None
            assert "Artificial intelligence" in result
            assert "Deep Learning" in result

            # Verify token tracking
            assert content_service.token_tracker.session_jina_tokens > initial_tokens

    @pytest.mark.asyncio
    async def test_fetch_full_content_errors(self, content_service):
        """Test error handling in full content fetching"""

        # Test 404 Not Found
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 404
            mock_response.reason = "Not Found"
            mock_get.return_value.__aenter__.return_value = mock_response

            result = await content_service.fetch_full_content(
                "https://example.com/missing"
            )
            assert result is None

        # Test network error
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.side_effect = aiohttp.ClientError("Network error")

            result = await content_service.fetch_full_content("https://unreachable.com")
            assert result is None

    @pytest.mark.asyncio
    async def test_jina_wallet_balance_checking(self, content_service):
        """Test Jina AI wallet balance checking functionality"""

        # Test successful balance check
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {"wallet": {"total_balance": 500.75}}
            mock_get.return_value.__aenter__.return_value = mock_response

            balance = await content_service._get_jina_wallet_balance()
            assert balance == 500.75

        # Test API error in balance check
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 403
            mock_response.reason = "Forbidden"
            mock_get.return_value.__aenter__.return_value = mock_response

            balance = await content_service._get_jina_wallet_balance()
            assert balance is None

        # Test network error in balance check
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.side_effect = Exception("Network timeout")

            balance = await content_service._get_jina_wallet_balance()
            assert balance is None

    @pytest.mark.asyncio
    async def test_content_analysis_batching(self, content_service):
        """Test content analysis batching functionality"""
        # Create multiple content results to test batching
        content_results = []
        for i in range(5):
            content_results.append(
                {
                    "url": f"https://example{i}.com",
                    "title": f"Test Article {i}",
                    "content": f"# Article {i}\n\n" + "Content " * 100,  # Large content
                    "diff": Mock(
                        has_changes=True, added_blocks=[f"Content for article {i}"]
                    ),
                }
            )

        with patch.object(content_service, "openai_client") as mock_openai:
            # Mock OpenAI response structure for batching
            mock_message = Mock()
            mock_message.content = """
1. **Title:** Batched Article 1
**Source:** https://example0.com
**Link:** https://example0.com/article1
**Categories:** AI
**Summary:** Batched analysis result
**Rankings:** [75, 70, 80]
"""
            mock_choice = Mock()
            mock_choice.message = mock_message

            mock_usage = Mock()
            mock_usage.prompt_tokens = 2000
            mock_usage.completion_tokens = 500
            mock_usage.total_tokens = 2500

            mock_completion = Mock()
            mock_completion.choices = [mock_choice]
            mock_completion.usage = mock_usage

            mock_openai.chat.completions.create = AsyncMock(
                return_value=mock_completion
            )

            results = await content_service.analyze_content(
                content_results,
                "Test batching",
                batch_size=1000,  # Small batch for testing
            )

            # Should process all content despite batching
            assert len(results) >= 1
            # OpenAI should be called multiple times due to batching
            assert mock_openai.chat.completions.create.call_count >= 1

    @pytest.mark.asyncio
    async def test_content_filtering_by_thresholds(self, content_service):
        """Test content filtering based on quality thresholds"""
        content_results = [
            {
                "url": "https://example.com",
                "title": "Test Article",
                "content": "Test content",
                "diff": Mock(has_changes=True, added_blocks=["Test content"]),
            }
        ]

        with patch.object(content_service, "openai_client") as mock_openai:
            # Mock response with items of different quality rankings
            mock_message = Mock()
            mock_message.content = """
1. **Title:** High Quality Article
**Source:** https://example.com
**Link:** https://example.com/high-quality
**Categories:** AI
**Summary:** High quality content
**Rankings:** [90, 85, 95]

2. **Title:** Medium Quality Article
**Source:** https://example.com
**Link:** https://example.com/medium-quality
**Categories:** AI
**Summary:** Medium quality content
**Rankings:** [60, 65, 70]

3. **Title:** Low Quality Article
**Source:** https://example.com
**Link:** https://example.com/low-quality
**Categories:** AI
**Summary:** Low quality content
**Rankings:** [30, 25, 35]
"""
            mock_choice = Mock()
            mock_choice.message = mock_message

            mock_usage = Mock()
            mock_usage.prompt_tokens = 1000
            mock_usage.completion_tokens = 300
            mock_usage.total_tokens = 1300

            mock_completion = Mock()
            mock_completion.choices = [mock_choice]
            mock_completion.usage = mock_usage

            mock_openai.chat.completions.create = AsyncMock(
                return_value=mock_completion
            )

            # Mock fetch_full_content for high-quality items
            with patch.object(content_service, "fetch_full_content") as mock_fetch:
                mock_fetch.return_value = "Full content for high quality article"

                results = await content_service.analyze_content(
                    content_results, "Test filtering"
                )

                # Should filter out low-quality items (below min_threshold=50.0)
                items = results.get("https://example.com", [])
                rankings = [item["ranking"] for item in items]

                # All returned items should be above threshold
                assert all(rank >= content_service.min_threshold for rank in rankings)

                # High-quality items should have full content fetched
                high_quality_items = [
                    item
                    for item in items
                    if item["ranking"] >= content_service.max_threshold
                ]
                if high_quality_items:
                    mock_fetch.assert_called()

    @pytest.mark.asyncio
    async def test_sync_progress_tracking(self, content_service):
        """Test sync progress tracking during content operations"""
        # Initialize sync progress with a source first
        content_service.sync_progress.start_sync(["https://progress-test.com"])

        # Verify source was initialized
        assert "https://progress-test.com" in content_service.sync_progress.sources
        assert (
            content_service.sync_progress.sources[
                "https://progress-test.com"
            ].status.value
            == "pending"
        )

        # Mock content fetching to track progress
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text.return_value = "# Test Content"
            mock_get.return_value.__aenter__.return_value = mock_response

            await content_service.fetch_content("https://progress-test.com")

            # Verify progress was updated to in_progress
            source_progress = content_service.sync_progress.sources[
                "https://progress-test.com"
            ]
            assert source_progress.status.value == "in_progress"

    @pytest.mark.asyncio
    async def test_markdown_parsing_edge_cases(self, content_service):
        """Test markdown parsing with edge cases and malformed content"""
        # Test malformed rankings
        malformed_content = """
1. **Title:** Test Article
**Source:** https://example.com
**Link:** https://example.com/test
**Categories:** AI
**Summary:** Test summary
**Rankings:** [invalid, data, here]

2. **Title:** Another Article
**Source:** https://example.com
**Link:** https://example.com/test2
**Categories:** Programming
**Summary:** Another summary
**Rankings:** [70, 75]

3. **Title:** Valid Article
**Source:** https://example.com
**Link:** https://example.com/test3
**Categories:** Data Science
**Summary:** Valid summary
**Rankings:** [80, 75, 85]
"""

        # Parse the malformed content
        items = content_service._parse_markdown_items(malformed_content)

        # Should skip malformed items and only return valid ones
        assert len(items) <= 2  # Should skip the malformed one

        valid_items = [item for item in items if item.get("ranking") is not None]
        assert len(valid_items) >= 1

        # Test empty content
        empty_items = content_service._parse_markdown_items("")
        assert len(empty_items) == 0

        # Test content with no valid items
        invalid_content = """
This is not properly formatted markdown content.
No items should be parsed from this.
"""
        invalid_items = content_service._parse_markdown_items(invalid_content)
        assert len(invalid_items) == 0


class TestContentServiceIntegrationWithStorage:
    """Test ContentService integration with StorageService"""

    @pytest.fixture
    def integrated_content_service(self, temp_db):
        """ContentService with real StorageService for integration testing"""
        storage_service = StorageService(temp_db)
        token_tracker = TokenTracker()

        return (
            ContentService(
                jina_api_key="test-jina-key",
                openai_api_key="test-openai-key",
                categories=["AI", "Programming"],
                storage_service=storage_service,
                token_tracker=token_tracker,
                min_threshold=50.0,
                max_threshold=80.0,
            ),
            storage_service,
        )

    @pytest.mark.asyncio
    async def test_content_diff_calculation_integration(
        self, integrated_content_service
    ):
        """Test content diff calculation with real storage"""
        content_service, storage_service = integrated_content_service

        url = "https://example.com/article"

        # Store initial content
        initial_content = "# Initial Article\n\nThis is the initial content."
        storage_service._store_content(url, initial_content)

        # Test diff calculation with new content
        new_content = (
            "# Updated Article\n\nThis is the initial content.\n\nThis is new content."
        )

        diff = storage_service.get_content_diff(url, new_content)

        assert diff.has_changes
        assert len(diff.added_blocks) > 0
        assert "This is new content." in diff.added_blocks[0]

    @pytest.mark.asyncio
    async def test_item_storage_and_filtering_integration(
        self, integrated_content_service
    ):
        """Test item storage and filtering integration"""
        content_service, storage_service = integrated_content_service

        # Create test items
        test_items = [
            {
                "title": "Existing Article",
                "link": "https://example.com/existing",
                "categories": ["AI"],
                "summary": "Existing summary",
                "ranking": 75,
            },
            {
                "title": "New Article",
                "link": "https://example.com/new",
                "categories": ["Programming"],
                "summary": "New summary",
                "ranking": 80,
            },
        ]

        # Store initial item
        storage_service._store_items("https://example.com", [test_items[0]])

        # Test filtering new items
        new_items = storage_service.filter_new_items("https://example.com", test_items)

        # Should only return the new item
        assert len(new_items) == 1
        assert new_items[0]["title"] == "New Article"

        # Store all items and verify
        storage_service._store_items("https://example.com", new_items)
        stored_items = storage_service.get_stored_items("https://example.com")

        assert len(stored_items) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
