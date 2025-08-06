"""
Plugin system for textual-snapshots with AI-ready architecture.

Provides extensible plugin interfaces that enable custom workflows,
AI integration, and future enhancements without breaking core functionality.
Designed based on ceremony recommendations for clean architecture.
"""

from typing import TYPE_CHECKING, Any, Protocol

from .types import AppContext

# Forward reference to avoid circular import
if TYPE_CHECKING:
    from .capture import CaptureResult
else:
    CaptureResult = Any


class CapturePlugin(Protocol):
    """
    Plugin interface for screenshot capture lifecycle hooks.

    Enables extensibility for AI integration, custom validation,
    training data collection, and workflow customization without
    modifying core capture functionality.
    """

    async def pre_capture(self, context: str, app_context: AppContext) -> dict[str, Any]:
        """
        Called before screenshot capture begins.

        Perfect hook for AI context preparation, state analysis,
        and pre-capture validation or setup.

        Args:
            context: Context description for the capture
            app_context: Application context being captured

        Returns:
            Dict[str, Any]: Metadata to pass to post_capture hook
        """
        ...

    async def post_capture(self, result: CaptureResult, metadata: dict[str, Any]) -> None:
        """
        Called after screenshot capture completes.

        Perfect hook for AI analysis, quality assessment,
        result enhancement, and training data collection.

        Args:
            result: Screenshot capture result (can be modified)
            metadata: Metadata from pre_capture hook
        """
        ...

    async def on_success(self, result: CaptureResult) -> None:
        """
        Called when screenshot capture succeeds.

        Ideal hook for training data collection, success pattern
        analysis, and positive feedback processing.

        Args:
            result: Successful capture result
        """
        ...

    async def on_failure(self, error: Exception, context: str) -> None:
        """
        Called when screenshot capture fails.

        Essential hook for error analysis, failure pattern
        detection, and automated error recovery.

        Args:
            error: Exception that caused the failure
            context: Context description where failure occurred
        """
        ...


class BasePlugin:
    """
    Abstract base class for plugins with optional hook implementation.

    Plugins can inherit from this class and only implement the hooks
    they need, providing flexibility and simplicity.
    """

    async def pre_capture(self, context: str, app_context: AppContext) -> dict[str, Any]:
        """Default pre_capture implementation returns empty metadata."""
        return {}

    async def post_capture(self, result: CaptureResult, metadata: dict[str, Any]) -> None:
        """Default post_capture implementation does nothing."""
        pass

    async def on_success(self, result: CaptureResult) -> None:
        """Default on_success implementation does nothing."""
        pass

    async def on_failure(self, error: Exception, context: str) -> None:
        """Default on_failure implementation does nothing."""
        pass


class ValidationPlugin(BasePlugin):
    """
    Plugin for screenshot validation and quality checking.

    Example plugin demonstrating validation patterns that could
    be enhanced with AI analysis in future versions.
    """

    def __init__(
        self,
        min_file_size: int = 1024,  # 1KB minimum
        max_file_size: int = 10 * 1024 * 1024,  # 10MB maximum
        require_content: bool = True,
    ):
        self.min_file_size = min_file_size
        self.max_file_size = max_file_size
        self.require_content = require_content

    async def post_capture(self, result: CaptureResult, metadata: dict[str, Any]) -> None:
        """Validate screenshot quality and set quality metadata."""
        if not result.success or not result.screenshot_path:
            return

        validation_results: dict[str, Any] = {
            "file_size_valid": True,
            "content_detected": True,
            "quality_score": 1.0,
            "validation_errors": [],
        }

        # File size validation
        if result.file_size_bytes < self.min_file_size:
            validation_results["file_size_valid"] = False
            validation_results["validation_errors"].append(
                f"File size {result.file_size_bytes} below minimum {self.min_file_size}"
            )

        if result.file_size_bytes > self.max_file_size:
            validation_results["file_size_valid"] = False
            validation_results["validation_errors"].append(
                f"File size {result.file_size_bytes} exceeds maximum {self.max_file_size}"
            )

        # Basic content validation (could be enhanced with AI)
        if self.require_content and result.file_size_bytes < 512:
            validation_results["content_detected"] = False
            validation_results["validation_errors"].append("Screenshot appears to be empty")

        # Calculate quality score
        if validation_results["validation_errors"]:
            validation_results["quality_score"] = 0.5

        # Enhance result with validation metadata
        if not result.ai_metadata:
            result.ai_metadata = {}
        result.ai_metadata.update(validation_results)


class LoggingPlugin(BasePlugin):
    """
    Plugin for comprehensive capture logging and monitoring.

    Demonstrates plugin patterns for monitoring and could be
    enhanced with AI-powered analytics in future versions.
    """

    def __init__(self, log_level: str = "INFO"):
        import logging

        self.logger = logging.getLogger(f"textual_snapshots.{self.__class__.__name__}")
        self.logger.setLevel(getattr(logging, log_level.upper()))

    async def pre_capture(self, context: str, app_context: AppContext) -> dict[str, Any]:
        """Log capture start and collect timing metadata."""
        import time

        self.logger.info(
            f"Starting screenshot capture: app={app_context.context_name}, context={context}"
        )

        return {"start_time": time.time()}

    async def post_capture(self, result: CaptureResult, metadata: dict[str, Any]) -> None:
        """Log capture completion with timing and result details."""
        import time

        duration = time.time() - metadata.get("start_time", 0)

        if result.success:
            self.logger.info(
                f"Screenshot capture succeeded: "
                f"path={result.screenshot_path}, "
                f"size={result.file_size_bytes}, "
                f"duration={duration:.2f}s, "
                f"cached={result.cache_hit}"
            )
        else:
            self.logger.error(
                f"Screenshot capture failed: error={result.error_message}, duration={duration:.2f}s"
            )

    async def on_failure(self, error: Exception, context: str) -> None:
        """Log detailed failure information."""
        self.logger.error(
            f"Capture failure in context '{context}': {error.__class__.__name__}: {str(error)}"
        )


class MetricsPlugin(BasePlugin):
    """
    Plugin for capture metrics collection and performance monitoring.

    Collects statistics that could be enhanced with AI analysis
    for performance optimization and pattern detection.
    """

    def __init__(self) -> None:
        self.capture_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.cache_hit_count = 0
        self.total_file_size = 0
        self.total_duration = 0.0

    async def pre_capture(self, context: str, app_context: AppContext) -> dict[str, Any]:
        """Start timing and increment counters."""
        import time

        self.capture_count += 1
        return {"metrics_start_time": time.time()}

    async def post_capture(self, result: CaptureResult, metadata: dict[str, Any]) -> None:
        """Update metrics with capture results."""
        import time

        duration = time.time() - metadata.get("metrics_start_time", 0)
        self.total_duration += duration

        if result.success:
            self.success_count += 1
            self.total_file_size += result.file_size_bytes

            if result.cache_hit:
                self.cache_hit_count += 1

    async def on_failure(self, error: Exception, context: str) -> None:
        """Update failure metrics."""
        self.failure_count += 1

    def get_metrics(self) -> dict[str, Any]:
        """Get collected metrics summary."""
        return {
            "total_captures": self.capture_count,
            "successful_captures": self.success_count,
            "failed_captures": self.failure_count,
            "cache_hits": self.cache_hit_count,
            "success_rate": self.success_count / max(self.capture_count, 1),
            "cache_hit_rate": self.cache_hit_count / max(self.success_count, 1),
            "average_file_size": self.total_file_size / max(self.success_count, 1),
            "average_duration": self.total_duration / max(self.capture_count, 1),
        }


# Future AI-ready plugin example (not implemented in Phase 1)
class AIAnalysisPlugin(BasePlugin):
    """
    Placeholder for future AI analysis plugin.

    This class demonstrates the architecture for AI integration
    using the plugin system without requiring AI dependencies
    in the current implementation.
    """

    def __init__(self) -> None:
        # Future: Initialize PydanticAI agent here
        self.ai_available = False

    async def post_capture(self, result: CaptureResult, metadata: dict[str, Any]) -> None:
        """
        Future: AI analysis of screenshot quality and content.

        This hook would integrate with PydanticAI agents to:
        - Analyze visual quality and rendering issues
        - Detect UI elements and layout problems
        - Generate quality scores and improvement suggestions
        - Collect training data for continuous improvement
        """
        if not self.ai_available:
            return

        # Future implementation would:
        # 1. Use PydanticAI agent with multimodal model
        # 2. Analyze screenshot for quality and content
        # 3. Generate structured analysis results
        # 4. Enhance result.ai_metadata with AI insights
        pass

    async def on_success(self, result: CaptureResult) -> None:
        """Future: Collect successful captures for training data."""
        if not self.ai_available:
            return

        # Future implementation would:
        # 1. Collect positive examples for training
        # 2. Analyze success patterns
        # 3. Build quality baselines
        pass
