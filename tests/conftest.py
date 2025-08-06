"""
Pytest configuration and fixtures for textual-snapshots testing.

Provides comprehensive test fixtures for screenshot capture testing,
including deterministic test apps, mock contexts, and test utilities.
"""

import asyncio
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from textual.app import App, ComposeResult
from textual.widgets import Button, Static

from textual_snapshots.capture import BasicAppContext, ScreenshotCapture
from textual_snapshots.plugins import BasePlugin
from textual_snapshots.types import AppContext


class PredictableTestApp(App):
    """Deterministic Textual app that produces consistent visual output."""

    def compose(self) -> ComposeResult:
        yield Static("PREDICTABLE_CONTENT", id="test-content")
        yield Static("Version: 1.0.0", id="version")
        yield Button("TEST_BUTTON", id="test-button")


class InteractiveTestApp(App):
    """Test app for interaction testing."""

    def __init__(self):
        super().__init__()
        self.button_clicked = False

    def compose(self) -> ComposeResult:
        yield Static("Interactive Test App", id="title")
        yield Button("Click Me", id="click-button")
        yield Static("Not Clicked", id="status")

    def on_button_pressed(self, event):
        self.button_clicked = True
        status = self.query_one("#status", Static)
        status.update("Clicked!")


class MockAppContext:
    """Mock AppContext for testing without real app dependencies."""

    def __init__(
        self,
        app_id: str = "test_app",
        context_name: str = "test_context",
        metadata: dict[str, Any] = None,
    ):
        self._app_id = app_id
        self._context_name = context_name
        self._metadata = metadata or {"test": True}
        self._app_instance = PredictableTestApp()

    @property
    def app_id(self) -> str:
        return self._app_id

    @property
    def context_name(self) -> str:
        return self._context_name

    def get_state_hash(self) -> str:
        return "test_hash_123"

    def get_metadata(self) -> dict[str, Any]:
        return self._metadata

    def get_app_instance(self) -> App:
        return self._app_instance


class TestPlugin(BasePlugin):
    """Test plugin for verifying plugin system functionality."""

    def __init__(self):
        self.pre_capture_called = False
        self.post_capture_called = False
        self.on_success_called = False
        self.on_failure_called = False
        self.pre_capture_metadata = {}
        self.post_capture_result = None
        self.success_result = None
        self.failure_error = None

    async def pre_capture(self, context: str, app_context: AppContext) -> dict[str, Any]:
        self.pre_capture_called = True
        self.pre_capture_metadata = {"plugin_test": True, "context": context}
        return self.pre_capture_metadata

    async def post_capture(self, result, metadata: dict[str, Any]) -> None:
        self.post_capture_called = True
        self.post_capture_result = result

    async def on_success(self, result) -> None:
        self.on_success_called = True
        self.success_result = result

    async def on_failure(self, error: Exception, context: str) -> None:
        self.on_failure_called = True
        self.failure_error = error


@pytest.fixture
def temp_screenshots_dir():
    """Temporary directory for screenshot testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def predictable_app():
    """Fixture providing a deterministic test app."""
    return PredictableTestApp


@pytest.fixture
def interactive_app():
    """Fixture providing an interactive test app."""
    return InteractiveTestApp


@pytest.fixture
def mock_app_context():
    """Fixture providing a mock AppContext."""
    return MockAppContext()


@pytest.fixture
def basic_app_context(predictable_app):
    """Fixture providing a basic AppContext with test app."""
    return BasicAppContext(
        app_source=predictable_app, name="test_app", metadata={"test_mode": True}
    )


@pytest.fixture
def screenshot_capture(temp_screenshots_dir):
    """Fixture providing a ScreenshotCapture instance with temp directory."""
    return ScreenshotCapture(base_directory=temp_screenshots_dir)


@pytest.fixture
def test_plugin():
    """Fixture providing a test plugin for verification."""
    return TestPlugin()


@pytest.fixture
def screenshot_capture_with_plugin(temp_screenshots_dir, test_plugin):
    """Fixture providing ScreenshotCapture with test plugin."""
    return ScreenshotCapture(base_directory=temp_screenshots_dir, plugins=[test_plugin])


@pytest.fixture
def mock_pilot():
    """Mock Textual pilot for interaction testing."""
    pilot = AsyncMock()
    pilot.press = AsyncMock()
    pilot.click = AsyncMock()
    pilot.hover = AsyncMock()
    pilot.app = MagicMock()
    pilot.app.save_screenshot = MagicMock()
    return pilot


@pytest.fixture
def mock_successful_screenshot(temp_screenshots_dir):
    """Create a mock successful screenshot file."""
    screenshot_path = temp_screenshots_dir / "test_screenshot.svg"
    screenshot_path.write_text('<svg><rect width="100" height="100" fill="blue"/></svg>')
    return screenshot_path


@pytest.fixture(autouse=True)
def setup_logging():
    """Setup logging for tests."""
    import logging

    logging.basicConfig(level=logging.DEBUG)


# Event loop fixture for async tests
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Utility functions for tests
def create_test_screenshot(path: Path, content: str = None) -> Path:
    """Create a test screenshot file with specified content."""
    if content is None:
        content = (
            '<svg width="800" height="600"><rect width="100%" height="100%" fill="white"/></svg>'
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path


def assert_screenshot_file_valid(screenshot_path: Path) -> None:
    """Assert that a screenshot file exists and has reasonable content."""
    assert screenshot_path.exists(), f"Screenshot file does not exist: {screenshot_path}"
    assert screenshot_path.stat().st_size > 0, "Screenshot file is empty"

    # Basic SVG validation
    if screenshot_path.suffix == ".svg":
        content = screenshot_path.read_text()
        assert content.startswith("<svg"), "SVG file does not start with <svg tag"
        assert "</svg>" in content, "SVG file does not contain closing </svg> tag"


def assert_plugin_hooks_called(plugin: TestPlugin, success: bool = True) -> None:
    """Assert that plugin hooks were called appropriately."""
    assert plugin.pre_capture_called, "pre_capture hook was not called"
    assert plugin.post_capture_called, "post_capture hook was not called"

    if success:
        assert plugin.on_success_called, "on_success hook was not called"
        assert not plugin.on_failure_called, "on_failure hook should not be called on success"
    else:
        assert plugin.on_failure_called, "on_failure hook was not called"
        assert not plugin.on_success_called, "on_success hook should not be called on failure"
