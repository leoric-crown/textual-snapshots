"""
Core screenshot capture engine for Textual applications.

Provides professional visual testing capabilities with plugin extensibility,
extracted from Testinator's proven screenshot infrastructure with budget system
bloat removed and AI-ready architecture established.
"""

import asyncio
import hashlib
import json
import logging
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Optional, Union

from pydantic import BaseModel, Field
from textual.app import App
from textual.pilot import Pilot

from .types import AppContext

if TYPE_CHECKING:
    from .plugins import CapturePlugin

# Configure logging
logger = logging.getLogger(__name__)

# Cache TTL preserved from original (valuable for performance)
CACHE_TTL_SECONDS = 3600  # 1 hour cache TTL


class ScreenshotFormat(str, Enum):
    """Available screenshot capture formats."""

    SVG = "svg"
    PNG = "png"
    BOTH = "both"


# AppContext now imported from .types


class BasicAppContext:
    """
    Basic implementation of AppContext for generic Textual applications.

    Provides simple context management without session dependencies,
    suitable for community use and testing scenarios.
    """

    def __init__(
        self,
        app_source: Union[type[App[Any]], App[Any]],
        name: str = "generic_app",
        metadata: Optional[dict[str, Any]] = None,
    ):
        self.app_source = app_source
        self.name = name
        self.metadata = metadata or {}
        self._app_id = f"{name}_{id(app_source)}"

    @property
    def app_id(self) -> str:
        return self._app_id

    @property
    def context_name(self) -> str:
        return self.name

    def get_state_hash(self) -> str:
        """Generate simple hash based on app class and metadata."""
        state_data = {
            "app_class": self.app_source.__class__.__name__,
            "metadata": self.metadata,
            "timestamp": datetime.now(timezone.utc).isoformat()[:19],  # Minute precision
        }
        content_str = json.dumps(state_data, sort_keys=True, default=str)
        return hashlib.sha256(content_str.encode()).hexdigest()[:16]

    def get_metadata(self) -> dict[str, Any]:
        """Return rich context metadata for AI-ready processing."""
        # Get the actual class name, handling both class and instance
        if isinstance(self.app_source, type):
            app_class_name = self.app_source.__name__
        else:
            app_class_name = self.app_source.__class__.__name__

        return {
            "app_class": app_class_name,
            "context_name": self.name,
            "app_id": self.app_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **self.metadata,
        }

    def get_app_instance(self) -> App[Any]:
        """Return app instance, creating if necessary."""
        if isinstance(self.app_source, type):
            return self.app_source()
        return self.app_source


class CaptureResult(BaseModel):
    """
    Result of screenshot capture operation.

    Simplified from original ScreenshotResult with budget system components
    removed and AI-ready extensions added for future enhancement.
    """

    model_config = {"arbitrary_types_allowed": True}

    success: bool = Field(..., description="Whether capture was successful")
    screenshot_path: Optional[Path] = Field(
        None, description="Path to captured screenshot (primary format)"
    )

    # Format-specific paths
    svg_path: Optional[Path] = Field(None, description="Path to SVG screenshot")
    png_path: Optional[Path] = Field(None, description="Path to PNG screenshot")
    format: ScreenshotFormat = Field(default=ScreenshotFormat.SVG, description="Output format used")

    # File information
    file_size_bytes: int = Field(default=0, description="Size of primary screenshot file")
    svg_size_bytes: int = Field(default=0, description="Size of SVG file")
    png_size_bytes: int = Field(default=0, description="Size of PNG file")

    # Context and timing
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When screenshot was captured",
    )
    context: str = Field(..., description="Context of the screenshot")
    app_context: Any = Field(..., description="Application context used")

    # Error handling
    error_message: Optional[str] = Field(None, description="Error message if capture failed")
    cache_hit: bool = Field(default=False, description="Whether result was from cache")

    # AI-ready extensions (optional, default to None)
    ai_metadata: Optional[dict[str, Any]] = Field(
        None, description="AI-specific metadata and analysis results"
    )

    # Conversion metrics (preserved from original valuable functionality)
    conversion_time_ms: float = Field(
        default=0.0, description="Time taken for conversion if applicable"
    )


class ScreenshotCache(BaseModel):
    """Cache entry for screenshot operations - preserved from original."""

    content_hash: str = Field(..., description="Hash of app state for caching")
    screenshot_path: Path = Field(..., description="Path to cached screenshot")
    created_at: datetime = Field(..., description="When cache entry was created")
    access_count: int = Field(default=0, description="Number of times accessed")
    last_accessed: datetime = Field(..., description="Last access time")


class ScreenshotCapture:
    """
    Core screenshot capture engine with plugin extensibility.

    Extracted from Testinator's AgentScreenshotCapture with budget system
    completely removed and plugin architecture established for AI-ready
    extensibility without current AI dependencies.
    """

    def __init__(
        self, base_directory: Optional[Path] = None, plugins: Optional[list["CapturePlugin"]] = None
    ):
        """
        Initialize screenshot capture system.

        Args:
            base_directory: Base directory for screenshots (defaults to screenshots/)
            plugins: List of plugins for capture lifecycle extensibility
        """
        self.base_directory = base_directory or Path("screenshots")
        self.cache: dict[str, ScreenshotCache] = {}
        self.plugins = plugins or []

        # Plugin hooks - AI-ready architecture
        self._pre_capture_hooks: list[Callable[..., Any]] = []
        self._post_capture_hooks: list[Callable[..., Any]] = []
        self._on_success_hooks: list[Callable[..., Any]] = []
        self._on_failure_hooks: list[Callable[..., Any]] = []

        # Initialize plugin system and directory structure
        self._register_plugin_hooks()
        self._ensure_directory_structure()

    def _ensure_directory_structure(self) -> None:
        """Create required directory structure."""
        directories = [
            self.base_directory / "apps",
            self.base_directory / "contexts",
            self.base_directory / "cache",
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def _register_plugin_hooks(self) -> None:
        """Register plugin hooks for lifecycle integration."""
        self._pre_capture_hooks.clear()
        self._post_capture_hooks.clear()
        self._on_success_hooks.clear()
        self._on_failure_hooks.clear()

        for plugin in self.plugins:
            if hasattr(plugin, "pre_capture"):
                self._pre_capture_hooks.append(plugin.pre_capture)
            if hasattr(plugin, "post_capture"):
                self._post_capture_hooks.append(plugin.post_capture)
            if hasattr(plugin, "on_success"):
                self._on_success_hooks.append(plugin.on_success)
            if hasattr(plugin, "on_failure"):
                self._on_failure_hooks.append(plugin.on_failure)

    def register_plugin(self, plugin: "CapturePlugin") -> None:
        """Register a plugin for capture lifecycle hooks."""
        self.plugins.append(plugin)
        self._register_plugin_hooks()

    def _generate_content_hash(self, app_context: AppContext, context: str) -> str:
        """Generate hash for caching based on app state and context."""
        cache_data = {
            "app_id": app_context.app_id,
            "context": context,
            "state_hash": app_context.get_state_hash(),
            "metadata_summary": str(sorted(app_context.get_metadata().keys())),
        }

        content_str = json.dumps(cache_data, sort_keys=True, default=str)
        return hashlib.sha256(content_str.encode()).hexdigest()[:16]

    def _get_cache_entry(self, content_hash: str) -> Optional[ScreenshotCache]:
        """Get cache entry if valid and recent."""
        cache_entry = self.cache.get(content_hash)
        if not cache_entry:
            return None

        # Check if cache file still exists
        if not cache_entry.screenshot_path.exists():
            del self.cache[content_hash]
            return None

        # Check if cache is recent (within TTL)
        cache_age = datetime.now(timezone.utc) - cache_entry.created_at
        if cache_age.total_seconds() > CACHE_TTL_SECONDS:
            return None

        return cache_entry

    def _update_cache(self, content_hash: str, screenshot_path: Path) -> None:
        """Update cache with new screenshot."""
        now = datetime.now(timezone.utc)
        self.cache[content_hash] = ScreenshotCache(
            content_hash=content_hash,
            screenshot_path=screenshot_path,
            created_at=now,
            last_accessed=now,
        )

    def organize_screenshots(self, app_context: AppContext, context: str) -> Path:
        """
        Organize screenshots by app and context.

        Args:
            app_context: Application context for organization
            context: Context description for organization

        Returns:
            Path: Directory path for organized screenshots
        """
        # Create app-specific directory
        app_dir = self.base_directory / "apps" / app_context.context_name
        app_dir.mkdir(parents=True, exist_ok=True)

        # Create context-specific directory
        context_dir = app_dir / context
        context_dir.mkdir(parents=True, exist_ok=True)

        return context_dir

    async def _execute_pre_capture_hooks(
        self, context: str, app_context: AppContext
    ) -> dict[str, Any]:
        """Execute pre-capture plugin hooks."""
        metadata = {}

        for hook in self._pre_capture_hooks:
            try:
                hook_result = await hook(context, app_context)
                if isinstance(hook_result, dict):
                    metadata.update(hook_result)
            except Exception as e:
                logger.warning(f"Pre-capture hook failed: {e}")

        return metadata

    async def _execute_post_capture_hooks(
        self, result: CaptureResult, metadata: dict[str, Any]
    ) -> None:
        """Execute post-capture plugin hooks."""
        for hook in self._post_capture_hooks:
            try:
                await hook(result, metadata)
            except Exception as e:
                logger.warning(f"Post-capture hook failed: {e}")

    async def _execute_success_hooks(self, result: CaptureResult) -> None:
        """Execute success plugin hooks."""
        for hook in self._on_success_hooks:
            try:
                await hook(result)
            except Exception as e:
                logger.warning(f"Success hook failed: {e}")

    async def _execute_failure_hooks(self, error: Exception, context: str) -> None:
        """Execute failure plugin hooks."""
        for hook in self._on_failure_hooks:
            try:
                await hook(error, context)
            except Exception as e:
                logger.warning(f"Failure hook failed: {e}")

    async def capture_app_screenshot(
        self,
        app_context: AppContext,
        context: str = "capture",
        output_format: ScreenshotFormat = ScreenshotFormat.SVG,
        interactions: Optional[list[str]] = None,
    ) -> CaptureResult:
        """
        Capture screenshot of Textual application.

        Args:
            app_context: Application context for capture
            context: Context description for the capture
            output_format: Output format (SVG, PNG, or BOTH)
            interactions: Optional interaction sequence to perform

        Returns:
            CaptureResult: Result of capture operation
        """
        # Execute pre-capture hooks
        hook_metadata = await self._execute_pre_capture_hooks(context, app_context)

        # Check cache first (valuable performance optimization preserved)
        content_hash = self._generate_content_hash(app_context, context)
        cache_entry = self._get_cache_entry(content_hash)

        if cache_entry:
            # Update cache access stats
            cache_entry.access_count += 1
            cache_entry.last_accessed = datetime.now(timezone.utc)

            result = CaptureResult(
                success=True,
                screenshot_path=cache_entry.screenshot_path,
                svg_path=cache_entry.screenshot_path,
                png_path=None,
                context=context,
                app_context=app_context,
                file_size_bytes=cache_entry.screenshot_path.stat().st_size,
                svg_size_bytes=cache_entry.screenshot_path.stat().st_size,
                cache_hit=True,
                error_message=None,
                ai_metadata=None,
            )

            # Execute hooks for cached results
            await self._execute_post_capture_hooks(result, hook_metadata)
            await self._execute_success_hooks(result)

            return result

        try:
            # Generate filename with timestamp
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            screenshot_dir = self.organize_screenshots(app_context, context)
            screenshot_path = screenshot_dir / f"{context}_{timestamp}.svg"

            # Get app instance and capture screenshot
            app = app_context.get_app_instance()

            async with app.run_test() as pilot:
                # Let UI render fully (preserved from original)
                await asyncio.sleep(0.3)

                # Perform interactions if specified
                if interactions:
                    await self._perform_interactions(pilot, interactions)

                # Capture screenshot
                pilot.app.save_screenshot(str(screenshot_path))

            # Verify screenshot was created
            if not screenshot_path.exists():
                error_msg = "Screenshot file was not created"
                await self._execute_failure_hooks(Exception(error_msg), context)
                return CaptureResult(
                    success=False,
                    screenshot_path=None,
                    svg_path=None,
                    png_path=None,
                    context=context,
                    app_context=app_context,
                    error_message=error_msg,
                    ai_metadata=None,
                )

            # Update cache
            self._update_cache(content_hash, screenshot_path)

            file_size = screenshot_path.stat().st_size

            result = CaptureResult(
                success=True,
                screenshot_path=screenshot_path,
                svg_path=screenshot_path,
                png_path=None,
                format=output_format,
                context=context,
                app_context=app_context,
                file_size_bytes=file_size,
                svg_size_bytes=file_size,
                error_message=None,
                ai_metadata=None,
            )

            # Execute post-capture hooks
            await self._execute_post_capture_hooks(result, hook_metadata)
            await self._execute_success_hooks(result)

            return result

        except Exception as e:
            error_msg = f"Screenshot capture failed: {str(e)}"
            await self._execute_failure_hooks(e, context)

            return CaptureResult(
                success=False,
                screenshot_path=None,
                svg_path=None,
                png_path=None,
                context=context,
                app_context=app_context,
                error_message=error_msg,
                ai_metadata=None,
            )

    async def _perform_interactions(self, pilot: Pilot[Any], interactions: list[str]) -> None:
        """Perform interaction sequence on pilot (enhanced from original)."""
        for interaction in interactions:
            if interaction.startswith("press:"):
                key = interaction.split(":", 1)[1]
                await pilot.press(key)
            elif interaction.startswith("click:"):
                selector = interaction.split(":", 1)[1]
                await pilot.click(selector)
            elif interaction.startswith("hover:"):
                selector = interaction.split(":", 1)[1]
                await pilot.hover(selector)
            elif interaction.startswith("type:"):
                text = interaction.split(":", 1)[1]
                for char in text:
                    await pilot.press(char)
                    await asyncio.sleep(0.05)  # Realistic typing speed
            elif interaction.startswith("wait:"):
                duration = float(interaction.split(":", 1)[1])
                await asyncio.sleep(duration)
            else:
                logger.warning(f"Unknown interaction command: {interaction}")

            # Small delay between interactions for stability
            await asyncio.sleep(0.1)

    def cleanup_old_cache_entries(self, max_age_hours: int = 24) -> int:
        """Clean up old cache entries (preserved valuable functionality)."""
        cutoff_time = datetime.now(timezone.utc).timestamp() - (max_age_hours * 3600)
        old_entries = []

        for content_hash, entry in self.cache.items():
            if entry.created_at.timestamp() < cutoff_time:
                old_entries.append(content_hash)

        for content_hash in old_entries:
            del self.cache[content_hash]

        return len(old_entries)

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics for monitoring (budget metrics removed)."""
        total_entries = len(self.cache)
        total_accesses = sum(entry.access_count for entry in self.cache.values())

        return {
            "total_cache_entries": total_entries,
            "total_cache_accesses": total_accesses,
            "cache_hit_rate": total_accesses / max(total_entries, 1),
            "average_access_count": total_accesses / max(total_entries, 1),
        }


# Convenience function for simple usage
async def capture_app_screenshot(
    app_source: Union[type[App[Any]], App[Any]],
    context: str = "capture",
    output_format: ScreenshotFormat = ScreenshotFormat.SVG,
    interactions: Optional[list[str]] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> CaptureResult:
    """
    Convenient function for capturing screenshots of Textual applications.

    Args:
        app_source: Textual app class or instance
        context: Context description for the capture
        output_format: Output format (SVG, PNG, or BOTH)
        interactions: Optional interaction sequence to perform
        metadata: Optional metadata for context

    Returns:
        CaptureResult: Result of capture operation
    """
    app_context = BasicAppContext(
        app_source=app_source,
        name=app_source.__class__.__name__ if hasattr(app_source, "__class__") else str(app_source),
        metadata=metadata,
    )

    capture = ScreenshotCapture()
    return await capture.capture_app_screenshot(
        app_context=app_context,
        context=context,
        output_format=output_format,
        interactions=interactions,
    )
