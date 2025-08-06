"""
Unit tests for core screenshot capture functionality.

Tests the ScreenshotCapture class and related components with focus on
budget system removal, plugin architecture, and generic app integration.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from textual_snapshots.capture import (
    BasicAppContext,
    CaptureResult,
    ScreenshotCapture,
    capture_app_screenshot,
)


class TestScreenshotCapture:
    """Test the core ScreenshotCapture class."""

    def test_initialization(self, temp_screenshots_dir):
        """Test ScreenshotCapture initialization without budget system."""
        capture = ScreenshotCapture(base_directory=temp_screenshots_dir)

        assert capture.base_directory == temp_screenshots_dir
        assert capture.cache == {}
        assert capture.plugins == []

        # Verify budget system components are NOT present
        assert not hasattr(capture, "daily_capture_count")
        assert not hasattr(capture, "max_daily_captures")
        assert not hasattr(capture, "_last_reset_date")

    def test_directory_structure_creation(self, temp_screenshots_dir):
        """Test that required directory structure is created."""
        ScreenshotCapture(base_directory=temp_screenshots_dir)

        expected_dirs = [
            temp_screenshots_dir / "apps",
            temp_screenshots_dir / "contexts",
            temp_screenshots_dir / "cache",
        ]

        for dir_path in expected_dirs:
            assert dir_path.exists(), f"Directory not created: {dir_path}"
            assert dir_path.is_dir(), f"Path is not a directory: {dir_path}"

    def test_plugin_registration(self, temp_screenshots_dir, test_plugin):
        """Test plugin registration and hook management."""
        capture = ScreenshotCapture(base_directory=temp_screenshots_dir)

        # Initially no plugins
        assert len(capture.plugins) == 0
        assert len(capture._pre_capture_hooks) == 0

        # Register plugin
        capture.register_plugin(test_plugin)

        assert len(capture.plugins) == 1
        assert test_plugin in capture.plugins
        assert len(capture._pre_capture_hooks) == 1
        assert len(capture._post_capture_hooks) == 1
        assert len(capture._on_success_hooks) == 1
        assert len(capture._on_failure_hooks) == 1

    def test_content_hash_generation(self, screenshot_capture, mock_app_context):
        """Test content hash generation for caching."""
        hash1 = screenshot_capture._generate_content_hash(mock_app_context, "test_context")
        hash2 = screenshot_capture._generate_content_hash(mock_app_context, "test_context")
        hash3 = screenshot_capture._generate_content_hash(mock_app_context, "different_context")

        # Same context should generate same hash
        assert hash1 == hash2
        assert len(hash1) == 16  # Hash is truncated to 16 characters

        # Different context should generate different hash
        assert hash1 != hash3

    def test_cache_operations(self, screenshot_capture, temp_screenshots_dir):
        """Test cache entry creation, retrieval, and expiration."""
        # Create a test screenshot file
        screenshot_path = temp_screenshots_dir / "test_cache.svg"
        screenshot_path.write_text('<svg><rect width="100" height="100"/></svg>')

        content_hash = "test_hash_123"

        # Test cache update
        screenshot_capture._update_cache(content_hash, screenshot_path)

        # Test cache retrieval
        cache_entry = screenshot_capture._get_cache_entry(content_hash)
        assert cache_entry is not None
        assert cache_entry.screenshot_path == screenshot_path
        assert cache_entry.content_hash == content_hash
        assert cache_entry.access_count == 0

        # Test cache miss for non-existent hash
        missing_entry = screenshot_capture._get_cache_entry("non_existent_hash")
        assert missing_entry is None

    def test_cache_cleanup(self, screenshot_capture, temp_screenshots_dir):
        """Test cleanup of old cache entries."""
        # Create test screenshot files
        old_screenshot = temp_screenshots_dir / "old_screenshot.svg"
        old_screenshot.write_text('<svg><rect width="100" height="100"/></svg>')

        recent_screenshot = temp_screenshots_dir / "recent_screenshot.svg"
        recent_screenshot.write_text('<svg><rect width="100" height="100"/></svg>')

        # Add entries to cache with different timestamps
        from datetime import timedelta

        old_time = datetime.now(timezone.utc) - timedelta(hours=25)
        recent_time = datetime.now(timezone.utc) - timedelta(minutes=30)

        # Manually create cache entries with specific timestamps
        from textual_snapshots.capture import ScreenshotCache

        old_cache = ScreenshotCache(
            content_hash="old_hash",
            screenshot_path=old_screenshot,
            created_at=old_time,
            last_accessed=old_time,
        )

        recent_cache = ScreenshotCache(
            content_hash="recent_hash",
            screenshot_path=recent_screenshot,
            created_at=recent_time,
            last_accessed=recent_time,
        )

        screenshot_capture.cache = {"old_hash": old_cache, "recent_hash": recent_cache}

        # Cleanup old entries (max_age_hours=24)
        cleaned_count = screenshot_capture.cleanup_old_cache_entries(max_age_hours=24)

        assert cleaned_count == 1
        assert "old_hash" not in screenshot_capture.cache
        assert "recent_hash" in screenshot_capture.cache

    def test_get_cache_stats(self, screenshot_capture, temp_screenshots_dir):
        """Test cache statistics without budget metrics."""
        # Initially empty cache
        stats = screenshot_capture.get_cache_stats()
        assert stats["total_cache_entries"] == 0
        assert stats["total_cache_accesses"] == 0
        assert stats["cache_hit_rate"] == 0.0

        # Add some cache entries
        screenshot_path = temp_screenshots_dir / "test_stats.svg"
        screenshot_path.write_text("<svg></svg>")

        screenshot_capture._update_cache("hash1", screenshot_path)
        screenshot_capture._update_cache("hash2", screenshot_path)

        # Simulate some accesses
        screenshot_capture.cache["hash1"].access_count = 3
        screenshot_capture.cache["hash2"].access_count = 1

        stats = screenshot_capture.get_cache_stats()
        assert stats["total_cache_entries"] == 2
        assert stats["total_cache_accesses"] == 4
        assert stats["cache_hit_rate"] == 2.0  # 4 accesses / 2 entries
        assert stats["average_access_count"] == 2.0

        # Verify budget-related metrics are NOT present
        assert "daily_captures_used" not in stats
        assert "daily_captures_remaining" not in stats

    def test_organize_screenshots(self, screenshot_capture, mock_app_context):
        """Test screenshot organization without session dependencies."""
        context = "test_organization"

        screenshot_dir = screenshot_capture.organize_screenshots(mock_app_context, context)

        expected_path = (
            screenshot_capture.base_directory / "apps" / mock_app_context.context_name / context
        )

        assert screenshot_dir == expected_path
        assert screenshot_dir.exists()
        assert screenshot_dir.is_dir()


class TestBasicAppContext:
    """Test the BasicAppContext implementation."""

    def test_initialization_with_class(self, predictable_app):
        """Test BasicAppContext initialization with app class."""
        context = BasicAppContext(
            app_source=predictable_app, name="test_app", metadata={"test": True}
        )

        assert context.context_name == "test_app"
        assert context.metadata == {"test": True}
        assert context.app_id.startswith("test_app_")

    def test_initialization_with_instance(self, predictable_app):
        """Test BasicAppContext initialization with app instance."""
        app_instance = predictable_app()
        context = BasicAppContext(app_source=app_instance, name="instance_test")

        assert context.context_name == "instance_test"
        assert context.get_app_instance() is app_instance

    def test_state_hash_generation(self, predictable_app):
        """Test state hash generation consistency."""
        context = BasicAppContext(
            app_source=predictable_app, name="hash_test", metadata={"version": "1.0"}
        )

        hash1 = context.get_state_hash()
        hash2 = context.get_state_hash()

        # Hashes should be consistent within the same minute
        assert len(hash1) == 16
        assert hash1 == hash2

    def test_metadata_collection(self, predictable_app):
        """Test rich metadata collection for AI-readiness."""
        context = BasicAppContext(
            app_source=predictable_app, name="metadata_test", metadata={"custom": "value"}
        )

        metadata = context.get_metadata()

        assert metadata["app_class"] == "PredictableTestApp"
        assert metadata["context_name"] == "metadata_test"
        assert metadata["custom"] == "value"
        assert "app_id" in metadata
        assert "timestamp" in metadata


class TestCaptureResult:
    """Test the CaptureResult model."""

    def test_successful_result_creation(self, mock_app_context, temp_screenshots_dir):
        """Test creation of successful capture result."""
        screenshot_path = temp_screenshots_dir / "success_test.svg"
        screenshot_path.write_text('<svg width="800" height="600"></svg>')

        result = CaptureResult(
            success=True,
            screenshot_path=screenshot_path,
            svg_path=screenshot_path,
            context="test_success",
            app_context=mock_app_context,
            file_size_bytes=screenshot_path.stat().st_size,
            svg_size_bytes=screenshot_path.stat().st_size,
        )

        assert result.success is True
        assert result.screenshot_path == screenshot_path
        assert result.svg_path == screenshot_path
        assert result.context == "test_success"
        assert result.file_size_bytes > 0
        assert result.error_message is None
        assert result.ai_metadata is None  # AI-ready but not required

    def test_failed_result_creation(self, mock_app_context):
        """Test creation of failed capture result."""
        result = CaptureResult(
            success=False,
            screenshot_path=None,
            context="test_failure",
            app_context=mock_app_context,
            error_message="Test error message",
        )

        assert result.success is False
        assert result.screenshot_path is None
        assert result.error_message == "Test error message"
        assert result.file_size_bytes == 0

    def test_ai_ready_extensions(self, mock_app_context):
        """Test AI-ready extensions in CaptureResult."""
        result = CaptureResult(
            success=True,
            context="ai_test",
            app_context=mock_app_context,
            ai_metadata={"quality_score": 0.95, "analysis": "good"},
        )

        assert result.ai_metadata is not None
        assert result.ai_metadata["quality_score"] == 0.95
        assert result.ai_metadata["analysis"] == "good"


class TestConvenienceFunction:
    """Test the convenience capture_app_screenshot function."""

    @pytest.mark.asyncio
    async def test_basic_capture_function(self, predictable_app, temp_screenshots_dir):
        """Test basic usage of capture_app_screenshot function."""
        with patch("textual_snapshots.capture.ScreenshotCapture") as mock_capture_class:
            mock_capture = MagicMock()
            mock_capture.capture_app_screenshot = AsyncMock()
            mock_capture.capture_app_screenshot.return_value = CaptureResult(
                success=True, context="test", app_context=MagicMock()
            )
            mock_capture_class.return_value = mock_capture

            result = await capture_app_screenshot(
                predictable_app, context="convenience_test", metadata={"test_mode": True}
            )

            assert mock_capture.capture_app_screenshot.called
            assert result.success is True

    @pytest.mark.asyncio
    async def test_capture_with_interactions(self, predictable_app):
        """Test capture function with interaction sequence."""
        with patch("textual_snapshots.capture.ScreenshotCapture") as mock_capture_class:
            mock_capture = MagicMock()
            mock_capture.capture_app_screenshot = AsyncMock()
            mock_capture.capture_app_screenshot.return_value = CaptureResult(
                success=True, context="interactions", app_context=MagicMock()
            )
            mock_capture_class.return_value = mock_capture

            interactions = ["click:#button", "wait:0.5", "press:enter"]

            result = await capture_app_screenshot(
                predictable_app, context="interaction_test", interactions=interactions
            )

            # Verify capture was called with interactions
            call_args = mock_capture.capture_app_screenshot.call_args
            assert call_args[1]["interactions"] == interactions
            assert result.success is True
