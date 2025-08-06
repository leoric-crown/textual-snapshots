"""
Unit tests for plugin system functionality.

Tests plugin interfaces, hook execution, and example plugin implementations
to ensure the AI-ready plugin architecture works correctly.
"""

from unittest.mock import MagicMock

import pytest

from textual_snapshots.capture import CaptureResult
from textual_snapshots.plugins import (
    BasePlugin,
    CapturePlugin,
    LoggingPlugin,
    MetricsPlugin,
    ValidationPlugin,
)


class TestCapturePluginProtocol:
    """Test the CapturePlugin protocol definition."""

    def test_plugin_protocol_methods(self):
        """Test that CapturePlugin protocol defines required methods."""
        # This test ensures the protocol is properly defined
        assert hasattr(CapturePlugin, "pre_capture")
        assert hasattr(CapturePlugin, "post_capture")
        assert hasattr(CapturePlugin, "on_success")
        assert hasattr(CapturePlugin, "on_failure")


class TestBasePlugin:
    """Test the BasePlugin abstract base class."""

    @pytest.mark.asyncio
    async def test_default_implementations(self, mock_app_context):
        """Test that BasePlugin provides default implementations."""
        plugin = BasePlugin()

        # Test default pre_capture returns empty dict
        result = await plugin.pre_capture("test", mock_app_context)
        assert result == {}

        # Test other methods don't raise errors
        await plugin.post_capture(MagicMock(), {})
        await plugin.on_success(MagicMock())
        await plugin.on_failure(Exception("test"), "context")


class TestValidationPlugin:
    """Test the ValidationPlugin implementation."""

    def test_initialization_with_defaults(self):
        """Test ValidationPlugin initialization with default values."""
        plugin = ValidationPlugin()

        assert plugin.min_file_size == 1024
        assert plugin.max_file_size == 10 * 1024 * 1024
        assert plugin.require_content is True

    def test_initialization_with_custom_values(self):
        """Test ValidationPlugin initialization with custom values."""
        plugin = ValidationPlugin(
            min_file_size=2048, max_file_size=5 * 1024 * 1024, require_content=False
        )

        assert plugin.min_file_size == 2048
        assert plugin.max_file_size == 5 * 1024 * 1024
        assert plugin.require_content is False

    @pytest.mark.asyncio
    async def test_validation_success(self, mock_app_context, temp_screenshots_dir):
        """Test validation of a good screenshot."""
        plugin = ValidationPlugin(min_file_size=30, max_file_size=1000000)  # Lower minimum for test

        # Create a valid result with enough content
        screenshot_path = temp_screenshots_dir / "valid_screenshot.svg"
        # Create a larger SVG to pass content detection (>512 bytes)
        large_svg = (
            '<svg width="800" height="600">'
            + '<rect x="1" y="1" width="10" height="10"/>' * 20
            + "</svg>"
        )
        screenshot_path.write_text(large_svg)

        result = CaptureResult(
            success=True,
            screenshot_path=screenshot_path,
            context="validation_test",
            app_context=mock_app_context,
            file_size_bytes=screenshot_path.stat().st_size,
        )

        await plugin.post_capture(result, {})

        assert result.ai_metadata is not None
        validation = result.ai_metadata
        assert validation["file_size_valid"] is True
        assert validation["content_detected"] is True
        assert validation["quality_score"] == 1.0
        assert len(validation["validation_errors"]) == 0

    @pytest.mark.asyncio
    async def test_validation_file_too_small(self, mock_app_context, temp_screenshots_dir):
        """Test validation failure for file that's too small."""
        plugin = ValidationPlugin(min_file_size=1000, max_file_size=1000000)

        # Create a small file
        screenshot_path = temp_screenshots_dir / "small_screenshot.svg"
        screenshot_path.write_text("<svg/>")

        result = CaptureResult(
            success=True,
            screenshot_path=screenshot_path,
            context="small_file_test",
            app_context=mock_app_context,
            file_size_bytes=screenshot_path.stat().st_size,
        )

        await plugin.post_capture(result, {})

        validation = result.ai_metadata
        assert validation["file_size_valid"] is False
        assert len(validation["validation_errors"]) > 0
        assert validation["quality_score"] == 0.5
        assert any("below minimum" in error for error in validation["validation_errors"])

    @pytest.mark.asyncio
    async def test_validation_file_too_large(self, mock_app_context, temp_screenshots_dir):
        """Test validation failure for file that's too large."""
        plugin = ValidationPlugin(min_file_size=100, max_file_size=500)

        # Create a large file
        screenshot_path = temp_screenshots_dir / "large_screenshot.svg"
        large_content = "<svg>" + "x" * 1000 + "</svg>"
        screenshot_path.write_text(large_content)

        result = CaptureResult(
            success=True,
            screenshot_path=screenshot_path,
            context="large_file_test",
            app_context=mock_app_context,
            file_size_bytes=screenshot_path.stat().st_size,
        )

        await plugin.post_capture(result, {})

        validation = result.ai_metadata
        assert validation["file_size_valid"] is False
        assert len(validation["validation_errors"]) > 0
        assert validation["quality_score"] == 0.5
        assert any("exceeds maximum" in error for error in validation["validation_errors"])

    @pytest.mark.asyncio
    async def test_validation_no_content(self, mock_app_context, temp_screenshots_dir):
        """Test validation failure for empty content."""
        plugin = ValidationPlugin(require_content=True)

        # Create an empty file
        screenshot_path = temp_screenshots_dir / "empty_screenshot.svg"
        screenshot_path.write_text("")

        result = CaptureResult(
            success=True,
            screenshot_path=screenshot_path,
            context="empty_content_test",
            app_context=mock_app_context,
            file_size_bytes=0,
        )

        await plugin.post_capture(result, {})

        validation = result.ai_metadata
        assert validation["content_detected"] is False
        assert len(validation["validation_errors"]) > 0
        assert validation["quality_score"] == 0.5
        assert any("appears to be empty" in error for error in validation["validation_errors"])

    @pytest.mark.asyncio
    async def test_validation_skips_failed_results(self, mock_app_context):
        """Test that validation skips failed capture results."""
        plugin = ValidationPlugin()

        result = CaptureResult(
            success=False,
            screenshot_path=None,
            context="failed_test",
            app_context=mock_app_context,
            error_message="Capture failed",
        )

        await plugin.post_capture(result, {})

        # Should not add validation metadata to failed results
        assert result.ai_metadata is None


class TestLoggingPlugin:
    """Test the LoggingPlugin implementation."""

    def test_initialization(self):
        """Test LoggingPlugin initialization."""
        plugin = LoggingPlugin(log_level="DEBUG")

        assert plugin.logger is not None
        assert plugin.logger.name == "textual_snapshots.LoggingPlugin"

    @pytest.mark.asyncio
    async def test_pre_capture_logging(self, mock_app_context):
        """Test pre-capture logging and timing metadata."""
        plugin = LoggingPlugin()

        metadata = await plugin.pre_capture("test_context", mock_app_context)

        assert "start_time" in metadata
        assert isinstance(metadata["start_time"], float)

    @pytest.mark.asyncio
    async def test_post_capture_success_logging(self, mock_app_context, temp_screenshots_dir):
        """Test post-capture logging for successful results."""
        plugin = LoggingPlugin()

        screenshot_path = temp_screenshots_dir / "success_log_test.svg"
        screenshot_path.write_text("<svg></svg>")

        result = CaptureResult(
            success=True,
            screenshot_path=screenshot_path,
            context="log_test",
            app_context=mock_app_context,
            file_size_bytes=screenshot_path.stat().st_size,
            cache_hit=False,
        )

        metadata = {"start_time": 1000.0}

        # This should not raise an exception
        await plugin.post_capture(result, metadata)

    @pytest.mark.asyncio
    async def test_post_capture_failure_logging(self, mock_app_context):
        """Test post-capture logging for failed results."""
        plugin = LoggingPlugin()

        result = CaptureResult(
            success=False,
            screenshot_path=None,
            context="log_failure_test",
            app_context=mock_app_context,
            error_message="Test failure",
        )

        metadata = {"start_time": 1000.0}

        # This should not raise an exception
        await plugin.post_capture(result, metadata)

    @pytest.mark.asyncio
    async def test_failure_logging(self):
        """Test failure logging."""
        plugin = LoggingPlugin()

        error = Exception("Test exception")

        # This should not raise an exception
        await plugin.on_failure(error, "test_context")


class TestMetricsPlugin:
    """Test the MetricsPlugin implementation."""

    def test_initialization(self):
        """Test MetricsPlugin initialization."""
        plugin = MetricsPlugin()

        assert plugin.capture_count == 0
        assert plugin.success_count == 0
        assert plugin.failure_count == 0
        assert plugin.cache_hit_count == 0
        assert plugin.total_file_size == 0
        assert plugin.total_duration == 0.0

    @pytest.mark.asyncio
    async def test_capture_counting(self, mock_app_context):
        """Test that captures are counted correctly."""
        plugin = MetricsPlugin()

        # Pre-capture should increment capture count and return timing
        metadata = await plugin.pre_capture("test", mock_app_context)

        assert plugin.capture_count == 1
        assert "metrics_start_time" in metadata

    @pytest.mark.asyncio
    async def test_success_metrics(self, mock_app_context, temp_screenshots_dir):
        """Test success metrics collection."""
        plugin = MetricsPlugin()

        screenshot_path = temp_screenshots_dir / "metrics_success.svg"
        screenshot_path.write_text('<svg width="100" height="100"></svg>')

        result = CaptureResult(
            success=True,
            screenshot_path=screenshot_path,
            context="metrics_test",
            app_context=mock_app_context,
            file_size_bytes=screenshot_path.stat().st_size,
            cache_hit=True,
        )

        # Simulate pre_capture call
        await plugin.pre_capture("test", mock_app_context)

        # Call post_capture
        metadata = {"metrics_start_time": 1000.0}
        await plugin.post_capture(result, metadata)

        assert plugin.success_count == 1
        assert plugin.cache_hit_count == 1
        assert plugin.total_file_size == screenshot_path.stat().st_size

    @pytest.mark.asyncio
    async def test_failure_metrics(self):
        """Test failure metrics collection."""
        plugin = MetricsPlugin()

        # Simulate capture attempt
        await plugin.pre_capture("test", MagicMock())

        # Simulate failure
        await plugin.on_failure(Exception("test"), "test_context")

        assert plugin.capture_count == 1
        assert plugin.failure_count == 1
        assert plugin.success_count == 0

    def test_metrics_calculation(self):
        """Test metrics calculation and reporting."""
        plugin = MetricsPlugin()

        # Simulate some activity
        plugin.capture_count = 10
        plugin.success_count = 8
        plugin.failure_count = 2
        plugin.cache_hit_count = 3
        plugin.total_file_size = 8000
        plugin.total_duration = 25.0

        metrics = plugin.get_metrics()

        assert metrics["total_captures"] == 10
        assert metrics["successful_captures"] == 8
        assert metrics["failed_captures"] == 2
        assert metrics["cache_hits"] == 3
        assert metrics["success_rate"] == 0.8
        assert metrics["cache_hit_rate"] == 0.375  # 3/8
        assert metrics["average_file_size"] == 1000.0  # 8000/8
        assert metrics["average_duration"] == 2.5  # 25.0/10

    def test_metrics_calculation_edge_cases(self):
        """Test metrics calculation with zero values."""
        plugin = MetricsPlugin()

        metrics = plugin.get_metrics()

        # Should handle division by zero gracefully
        assert metrics["total_captures"] == 0
        assert metrics["success_rate"] == 0.0
        assert metrics["cache_hit_rate"] == 0.0
        assert metrics["average_file_size"] == 0.0
        assert metrics["average_duration"] == 0.0


class TestPluginIntegration:
    """Test plugin integration with ScreenshotCapture."""

    @pytest.mark.asyncio
    async def test_plugin_hook_execution_order(
        self, screenshot_capture_with_plugin, mock_app_context, test_plugin
    ):
        """Test that plugin hooks are executed in correct order."""
        # The capture should succeed with mock context, so let's test success path
        await screenshot_capture_with_plugin.capture_app_screenshot(
            mock_app_context, "hook_order_test"
        )

        # Verify hooks were called in success scenario
        assert test_plugin.pre_capture_called
        assert test_plugin.post_capture_called
        assert test_plugin.on_success_called

        # Verify the context was passed correctly
        assert test_plugin.pre_capture_metadata["context"] == "hook_order_test"

    @pytest.mark.asyncio
    async def test_multiple_plugins_execution(self, temp_screenshots_dir, mock_app_context):
        """Test that multiple plugins are executed correctly."""
        from textual_snapshots.capture import ScreenshotCapture

        plugin1 = MetricsPlugin()
        plugin2 = ValidationPlugin()

        capture = ScreenshotCapture(base_directory=temp_screenshots_dir, plugins=[plugin1, plugin2])

        # Verify both plugins were registered
        assert len(capture.plugins) == 2
        assert len(capture._pre_capture_hooks) == 2  # Both have pre_capture (BasePlugin default)
        assert len(capture._post_capture_hooks) == 2  # Both have post_capture
        assert len(capture._on_failure_hooks) == 2  # Both have on_failure (BasePlugin default)

    @pytest.mark.asyncio
    async def test_plugin_hook_error_handling(self, screenshot_capture, mock_app_context):
        """Test that plugin hook errors don't break capture process."""

        class FailingPlugin(BasePlugin):
            async def pre_capture(self, context, app_context):
                raise Exception("Plugin error")

        failing_plugin = FailingPlugin()
        screenshot_capture.register_plugin(failing_plugin)

        # This should not raise an exception despite plugin failure
        # The hook execution should handle plugin errors gracefully

        # Test that hook execution handles errors
        metadata = await screenshot_capture._execute_pre_capture_hooks("test", mock_app_context)

        # Should return empty metadata when plugin fails
        assert isinstance(metadata, dict)
