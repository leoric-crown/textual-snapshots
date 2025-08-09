# API Reference

Complete documentation for textual-snapshots Python API and CLI commands.

## Overview

The textual-snapshots API provides programmatic access to all screenshot capture, comparison, and validation functionality. The API is designed for both simple use cases and complex testing workflows.

### Key Components

- **[Python API](#python-api)** - Core functions and classes for screenshot capture
- **[CLI Commands](#cli-commands)** - Command-line interface for batch operations
- **[Plugin System](#plugin-system)** - Extensible architecture for custom workflows
- **[Type Definitions](#type-definitions)** - Type hints and enums

### Quick Start

```python
from textual_snapshots import capture_app_screenshot
from my_app import MyTextualApp

# Basic screenshot
result = await capture_app_screenshot(MyTextualApp(), context="homepage")
print(f"Screenshot: {result.screenshot_path}")
```

---

## Python API

### `capture_app_screenshot()`

**Main function for capturing screenshots of Textual applications.**

#### Signature

```python
async def capture_app_screenshot(
    app_source: Type[App] | App,
    context: str = "capture",
    interactions: Optional[list[str]] = None,
    output_format: ScreenshotFormat = ScreenshotFormat.SVG,
    output_dir: Optional[Path] = None
) -> CaptureResult
```

#### Parameters

##### `app_source: Type[App] | App`

The Textual application to capture. Can be:

- **App class**: `MyApp` (will be instantiated)
- **App instance**: `MyApp()` (used directly)

```python
# App class (recommended)
result = await capture_app_screenshot(MyApp, context="homepage")

# App instance (for custom initialization)
app = MyApp(config=custom_config)
result = await capture_app_screenshot(app, context="configured")
```

##### `context: str = "capture"`

Context name for the screenshot, used in filename generation.

- **Default**: `"capture"`
- **Format**: `{context}_{timestamp}.svg`
- **Examples**: `"homepage"`, `"login_form"`, `"error_state"`

```python
# Creates: homepage_20250805_143021.svg
result = await capture_app_screenshot(MyApp, context="homepage")

# Creates: user_dashboard_20250805_143045.svg
result = await capture_app_screenshot(MyApp, context="user_dashboard")
```

##### `interactions: Optional[list[str]] = None`

User interaction sequence to perform before capturing screenshot.

**Supported commands:**

- `"click:SELECTOR"` - Click element by CSS selector
- `"type:TEXT"` - Type text into focused element
- `"press:KEY"` - Press keyboard key
- `"wait:SECONDS"` - Wait for specified duration

```python
# Simple click
result = await capture_app_screenshot(
    MyApp,
    context="button_clicked",
    interactions=["click:#submit-button"]
)

# Complex workflow
result = await capture_app_screenshot(
    MyApp,
    context="login_complete",
    interactions=[
        "click:#username",
        "type:user@example.com",
        "press:tab",
        "type:password123",
        "click:#login-button",
        "wait:2.0",  # Wait for redirect
        "press:enter"
    ]
)
```

##### `output_format: ScreenshotFormat = ScreenshotFormat.SVG`

Screenshot output format.

```python
from textual_snapshots import ScreenshotFormat

# SVG (default) - Vector format, smaller files
result = await capture_app_screenshot(MyApp, output_format=ScreenshotFormat.SVG)

# PNG - Raster format (requires Playwright)
result = await capture_app_screenshot(MyApp, output_format=ScreenshotFormat.PNG)

# Both formats
result = await capture_app_screenshot(MyApp, output_format=ScreenshotFormat.BOTH)
```

##### `output_dir: Optional[Path] = None`

Output directory for screenshots.

- **Default**: `./screenshots/`
- **Auto-created**: Directory created if it doesn't exist

```python
from pathlib import Path

# Default location
result = await capture_app_screenshot(MyApp)
# Saves to: ./screenshots/capture_*.svg

# Custom directory
result = await capture_app_screenshot(
    MyApp,
    output_dir=Path("./test-results/visual/")
)
# Saves to: ./test-results/visual/capture_*.svg
```

#### Returns: `CaptureResult`

```python
result = await capture_app_screenshot(MyApp, context="test")

print(result.success)           # bool: True if capture succeeded
print(result.screenshot_path)   # Path: Full path to screenshot file
print(result.file_size_bytes)   # int: File size in bytes
print(result.format)           # ScreenshotFormat: SVG, PNG, or BOTH
print(result.timestamp)        # datetime: UTC timestamp of capture
print(result.context)          # str: Context name used
```

#### Examples

##### Basic Usage

```python
import asyncio
from textual_snapshots import capture_app_screenshot
from my_app import MyApp

async def test_basic_screenshot():
    result = await capture_app_screenshot(MyApp, context="homepage")
    assert result.success
    assert result.screenshot_path.exists()
    print(f"Screenshot saved: {result.screenshot_path}")

asyncio.run(test_basic_screenshot())
```

##### With Interactions

```python
async def test_user_workflow():
    result = await capture_app_screenshot(
        MyApp,
        context="registration_flow",
        interactions=[
            "click:#register-tab",
            "click:#email-input",
            "type:newuser@example.com",
            "click:#password-input",
            "type:securepassword123",
            "click:#confirm-password",
            "type:securepassword123",
            "click:#terms-checkbox",
            "click:#register-button",
            "wait:1.5"  # Wait for success message
        ]
    )
    assert result.success
    return result
```

##### Error Handling

```python
async def test_with_error_handling():
    try:
        result = await capture_app_screenshot(
            MyApp,
            context="error_test",
            interactions=["click:#nonexistent-button"]
        )
        if not result.success:
            print(f"Capture failed: {result.error_message}")
    except Exception as e:
        print(f"Capture exception: {e}")
```

---

### `ScreenshotCapture`

**Advanced screenshot capture class with plugin support and configuration options.**

#### Class Definition

```python
class ScreenshotCapture:
    def __init__(
        self,
        plugins: Optional[list[CapturePlugin]] = None,
        output_dir: Optional[Path] = None,
        default_format: ScreenshotFormat = ScreenshotFormat.SVG
    )
```

#### Parameters

##### `plugins: Optional[list[CapturePlugin]] = None`

List of capture plugins for custom processing.

```python
from textual_snapshots import ScreenshotCapture
from textual_snapshots.plugins import CapturePlugin

class LoggingPlugin(CapturePlugin):
    async def pre_capture(self, app_source, metadata):
        print(f"Starting capture: {metadata.context}")

    async def post_capture(self, result, metadata):
        print(f"Completed: {result.screenshot_path}")

# Create capture instance with plugins
capture = ScreenshotCapture(plugins=[LoggingPlugin()])
```

##### `output_dir: Optional[Path] = None`

Default output directory for all captures.

```python
from pathlib import Path

# All screenshots go to custom directory
capture = ScreenshotCapture(output_dir=Path("./visual-tests/"))
```

##### `default_format: ScreenshotFormat = ScreenshotFormat.SVG`

Default format for all captures (can be overridden per capture).

```python
# All screenshots default to PNG
capture = ScreenshotCapture(default_format=ScreenshotFormat.PNG)
```

#### Methods

##### `async capture_app_screenshot()`

Same signature as standalone function, but uses instance configuration.

```python
capture = ScreenshotCapture(
    output_dir=Path("./screenshots/"),
    default_format=ScreenshotFormat.SVG
)

# Uses instance configuration
result = await capture.capture_app_screenshot(MyApp, context="test")

# Override instance defaults
result = await capture.capture_app_screenshot(
    MyApp,
    context="test",
    output_format=ScreenshotFormat.PNG,  # Override default
    output_dir=Path("./special/")        # Override default
)
```

#### Examples

##### Custom Validation Plugin

```python
from textual_snapshots import ScreenshotCapture
from textual_snapshots.plugins import CapturePlugin

class SizeValidationPlugin(CapturePlugin):
    async def post_capture(self, result, metadata):
        max_size = 1024 * 1024  # 1MB
        if result.file_size_bytes > max_size:
            print(f"Warning: Large screenshot {result.file_size_bytes:,} bytes")

        # Validate screenshot has content
        if result.file_size_bytes < 1000:  # Less than 1KB
            raise ValueError("Screenshot appears to be empty")

class TimingPlugin(CapturePlugin):
    def __init__(self):
        self.start_time = None

    async def pre_capture(self, app_source, metadata):
        import time
        self.start_time = time.time()

    async def post_capture(self, result, metadata):
        import time
        duration = time.time() - self.start_time
        print(f"Capture took {duration:.2f} seconds")

# Use plugins
capture = ScreenshotCapture(plugins=[
    SizeValidationPlugin(),
    TimingPlugin()
])

result = await capture.capture_app_screenshot(MyApp, context="validated")
```

---

### `CaptureResult`

**Result object returned by screenshot capture operations.**

#### Attributes

##### `success: bool`

Whether the capture operation succeeded.

```python
result = await capture_app_screenshot(MyApp)
if result.success:
    print("Capture successful!")
else:
    print(f"Capture failed: {result.error_message}")
```

##### `screenshot_path: Path`

Full path to the captured screenshot file.

```python
result = await capture_app_screenshot(MyApp, context="homepage")
print(f"Screenshot location: {result.screenshot_path}")
print(f"File exists: {result.screenshot_path.exists()}")

# Open in browser (macOS)
import subprocess
subprocess.run(["open", str(result.screenshot_path)])
```

##### `file_size_bytes: int`

Size of the screenshot file in bytes.

```python
result = await capture_app_screenshot(MyApp)
print(f"File size: {result.file_size_bytes:,} bytes")
print(f"File size: {result.file_size_bytes / 1024:.1f} KB")

# Check if file is reasonable size
if result.file_size_bytes > 1024 * 1024:  # 1MB
    print("Warning: Very large screenshot file")
elif result.file_size_bytes < 1000:  # 1KB
    print("Warning: Screenshot may be empty")
```

##### `format: ScreenshotFormat`

Format of the captured screenshot.

```python
from textual_snapshots import ScreenshotFormat

result = await capture_app_screenshot(MyApp, output_format=ScreenshotFormat.PNG)
print(f"Format: {result.format}")  # ScreenshotFormat.PNG

if result.format == ScreenshotFormat.SVG:
    print("Vector format - scalable")
elif result.format == ScreenshotFormat.PNG:
    print("Raster format - fixed resolution")
```

##### `timestamp: datetime`

UTC timestamp when the screenshot was captured.

```python
from datetime import timezone

result = await capture_app_screenshot(MyApp)
print(f"Captured at: {result.timestamp}")
print(f"Local time: {result.timestamp.astimezone()}")

# Check if capture is recent
import datetime
age = datetime.datetime.now(timezone.utc) - result.timestamp
print(f"Screenshot age: {age.total_seconds():.1f} seconds")
```

##### `context: str`

Context name used for the capture.

```python
result = await capture_app_screenshot(MyApp, context="user_dashboard")
print(f"Context: {result.context}")  # "user_dashboard"

# Generate report filename based on context
report_name = f"test_report_{result.context}.html"
```

##### `error_message: Optional[str]`

Error message if capture failed (None if successful).

```python
result = await capture_app_screenshot(BrokenApp)
if not result.success:
    print(f"Capture failed: {result.error_message}")
    # Log error for debugging
    import logging
    logging.error(f"Screenshot capture failed: {result.error_message}")
```

#### Methods

##### `matches_baseline(baseline_path: Path, tolerance: float = 0.95) -> bool`

Compare captured screenshot with a baseline image.

```python
result = await capture_app_screenshot(MyApp, context="homepage")

# Compare with baseline
baseline = Path("baselines/homepage_baseline.svg")
if result.matches_baseline(baseline, tolerance=0.95):
    print("✓ Visual regression test passed")
else:
    print("✗ Visual differences detected")
```

#### Examples

##### Complete Test with Result Validation

```python
async def test_complete_workflow():
    # Capture screenshot
    result = await capture_app_screenshot(
        MyApp,
        context="complete_test",
        interactions=[
            "click:#start-button",
            "wait:1.0",
            "type:test data",
            "press:enter"
        ]
    )

    # Validate result
    assert result.success, f"Capture failed: {result.error_message}"
    assert result.screenshot_path.exists(), "Screenshot file not found"
    assert result.file_size_bytes > 1000, "Screenshot appears empty"
    assert result.context == "complete_test", "Incorrect context"

    # Additional validations
    age_seconds = (datetime.now(timezone.utc) - result.timestamp).total_seconds()
    assert age_seconds < 60, "Screenshot not fresh"

    # Compare with baseline if exists
    baseline = Path(f"baselines/{result.context}_baseline.svg")
    if baseline.exists():
        assert result.matches_baseline(baseline, tolerance=0.95), \
               "Visual regression detected"

    print(f"✓ All validations passed: {result.screenshot_path}")
    return result
```

---

## Plugin System

### `CapturePlugin`

**Base class for creating custom capture plugins.**

#### Base Class Definition

```python
class CapturePlugin:
    async def pre_capture(self, app_source, metadata) -> None:
        """Called before screenshot capture."""
        pass

    async def post_capture(self, result: CaptureResult, metadata) -> None:
        """Called after screenshot capture."""
        pass

    async def on_error(self, error: Exception, metadata) -> None:
        """Called if capture fails."""
        pass
```

#### Plugin Lifecycle

1. **`pre_capture()`** - Called before app startup and screenshot
2. **Screenshot capture** - Core capture logic (handled by library)
3. **`post_capture()`** - Called after successful capture
4. **`on_error()`** - Called if any step fails

#### Plugin Examples

##### Logging Plugin

```python
import logging
from textual_snapshots.plugins import CapturePlugin

class DetailedLoggingPlugin(CapturePlugin):
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)

    async def pre_capture(self, app_source, metadata):
        self.logger.info(f"Starting capture: {metadata.context}")
        self.logger.debug(f"App: {app_source}, Format: {metadata.format}")

    async def post_capture(self, result, metadata):
        self.logger.info(
            f"Capture complete: {result.screenshot_path} "
            f"({result.file_size_bytes:,} bytes)"
        )

    async def on_error(self, error, metadata):
        self.logger.error(f"Capture failed for {metadata.context}: {error}")
```

##### Quality Validation Plugin

```python
from textual_snapshots.plugins import CapturePlugin

class QualityPlugin(CapturePlugin):
    def __init__(self, min_size_bytes=1000, max_size_bytes=10*1024*1024):
        self.min_size = min_size_bytes
        self.max_size = max_size_bytes

    async def post_capture(self, result, metadata):
        size = result.file_size_bytes

        if size < self.min_size:
            raise ValueError(
                f"Screenshot too small ({size} bytes) - may be empty or corrupted"
            )

        if size > self.max_size:
            raise ValueError(
                f"Screenshot too large ({size:,} bytes) - may indicate rendering issue"
            )

        # Validate file actually exists and is readable
        if not result.screenshot_path.exists():
            raise FileNotFoundError(f"Screenshot not found: {result.screenshot_path}")

        # Additional SVG validation
        if result.format == ScreenshotFormat.SVG:
            content = result.screenshot_path.read_text()
            if not content.strip().startswith('<?xml') and not content.strip().startswith('<svg'):
                raise ValueError("Invalid SVG format")
```

##### Cleanup Plugin

```python
from pathlib import Path
from datetime import datetime, timedelta
from textual_snapshots.plugins import CapturePlugin

class CleanupPlugin(CapturePlugin):
    def __init__(self, max_age_days=30, max_files=1000):
        self.max_age = timedelta(days=max_age_days)
        self.max_files = max_files

    async def post_capture(self, result, metadata):
        """Clean up old screenshots after each capture."""
        screenshots_dir = result.screenshot_path.parent
        await self._cleanup_old_files(screenshots_dir)

    async def _cleanup_old_files(self, directory: Path):
        """Remove old screenshot files."""
        now = datetime.now()
        svg_files = list(directory.glob("*.svg"))
        png_files = list(directory.glob("*.png"))
        all_files = svg_files + png_files

        # Remove files older than max_age
        for file_path in all_files:
            file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            if now - file_time > self.max_age:
                file_path.unlink()
                print(f"Cleaned up old screenshot: {file_path}")

        # If still too many files, remove oldest
        remaining_files = [f for f in all_files if f.exists()]
        if len(remaining_files) > self.max_files:
            # Sort by modification time
            remaining_files.sort(key=lambda f: f.stat().st_mtime)
            files_to_remove = remaining_files[:-self.max_files]

            for file_path in files_to_remove:
                file_path.unlink()
                print(f"Cleaned up excess screenshot: {file_path}")
```

#### Using Multiple Plugins

```python
from textual_snapshots import ScreenshotCapture

# Combine multiple plugins
capture = ScreenshotCapture(plugins=[
    DetailedLoggingPlugin(),
    QualityPlugin(min_size_bytes=2000, max_size_bytes=5*1024*1024),
    CleanupPlugin(max_age_days=14, max_files=500),
])

result = await capture.capture_app_screenshot(MyApp, context="production_test")
```

---

## CLI Commands

Complete documentation for all textual-snapshot CLI commands.

### Global Options

All commands support these global options:

```bash
textual-snapshot [GLOBAL_OPTIONS] COMMAND [COMMAND_OPTIONS]
```

#### Global Options

- `--verbose, -v` - Verbose output with detailed information
- `--quiet, -q` - Minimal output (only errors and results)
- `--version` - Show version and exit
- `--help` - Show help message

**Note**: `--verbose` and `--quiet` cannot be used together.

### Commands Overview

| Command               | Purpose                                | Quick Example                                             |
| --------------------- | -------------------------------------- | --------------------------------------------------------- |
| [`capture`](#capture) | Screenshot capture with auto-discovery | `textual-snapshot capture`                                |
| [`compare`](#compare) | Visual regression testing              | `textual-snapshot compare baseline.svg current.svg`       |
| [`migrate`](#migrate) | Migration from other frameworks        | `textual-snapshot migrate --from pytest-textual-snapshot` |
| [`convert`](#convert) | Format conversion (SVG ↔ PNG)          | `textual-snapshot convert input.svg --to png`             |

---

### `capture`

Capture screenshots of Textual applications with intelligent auto-discovery.

#### Usage

```bash
textual-snapshot capture [APP_PATH] [OPTIONS]
```

#### Arguments

- `APP_PATH` - Path to Python file containing Textual app (optional, auto-discovered if omitted)

#### Options

##### Basic Options

- `--context, -c TEXT` - Context name for screenshot (default: "capture")
- `--format, -f [svg|png|both]` - Output format (default: svg)
- `--output-dir, -o PATH` - Output directory (default: screenshots/)

##### Discovery Options

- `--interactive` - Interactive app selection when multiple apps found

##### Interaction Options

- `--interactions, -i TEXT` - Comma-separated interaction sequence

#### Examples

##### Basic Capture

```bash
# Auto-discover and capture
textual-snapshot capture

# Specific app file
textual-snapshot capture my_app.py

# Custom context name
textual-snapshot capture --context "homepage_v2"
```

##### Format Options

```bash
# PNG format (requires Playwright)
textual-snapshot capture --format png

# Both SVG and PNG
textual-snapshot capture --format both

# Custom output directory
textual-snapshot capture --output-dir ./visual-tests/
```

##### Interactive Screenshots

```bash
# Simple click
textual-snapshot capture --interactions "click:#button"

# Complex workflow
textual-snapshot capture --interactions "click:#username,type:user@example.com,press:tab,type:password123,click:#login"

# With timing
textual-snapshot capture --interactions "click:#button,wait:2.0,press:enter"
```

##### Auto-Discovery

```bash
# Interactive selection when multiple apps found
textual-snapshot capture --interactive

# Verbose output shows discovery process
textual-snapshot capture --verbose
```

#### Interaction Commands

The `--interactions` option supports these commands:

| Command          | Description                   | Example            |
| ---------------- | ----------------------------- | ------------------ |
| `click:SELECTOR` | Click element by CSS selector | `click:#button`    |
| `type:TEXT`      | Type text                     | `type:hello world` |
| `press:KEY`      | Press keyboard key            | `press:enter`      |
| `wait:SECONDS`   | Wait for specified duration   | `wait:1.5`         |

**Selector formats:**

- `#id` - Element with ID
- `.class` - Element with CSS class
- `tag` - HTML/widget tag name

#### Output

Successful capture displays:

```
✓ Screenshot captured successfully

Path: screenshots/homepage_20250805_143021.svg
Size: 15,234 bytes
Format: svg
Timestamp: 2025-08-05 14:30:21 UTC
```

---

### `compare`

Compare screenshots for visual regression detection with detailed reporting.

#### Usage

```bash
textual-snapshot compare BASELINE CURRENT [OPTIONS]
```

#### Arguments

- `BASELINE` - Baseline screenshot file or directory
- `CURRENT` - Current screenshot file or directory

#### Options

- `--threshold, -t FLOAT` - Similarity threshold 0.0-1.0 (default: 0.95)
- `--recursive, -r` - Compare directories recursively
- `--output-report PATH` - Save detailed JSON report

#### Examples

##### Single File Comparison

```bash
# Basic comparison
textual-snapshot compare baseline.svg current.svg

# Custom threshold (more sensitive)
textual-snapshot compare baseline.svg current.svg --threshold 0.99

# Less sensitive threshold
textual-snapshot compare baseline.svg current.svg --threshold 0.85
```

##### Directory Comparison

```bash
# Compare all files in directories
textual-snapshot compare baselines/ current/

# Recursive directory comparison
textual-snapshot compare baselines/ current/ --recursive

# Generate detailed report
textual-snapshot compare baselines/ current/ --output-report report.json
```

#### Output

##### Comparison Results Table

```
Comparison Results
┌─────────────────────────┬────────────┬────────┬─────────────────────┐
│ File                    │ Similarity │ Status │ Notes               │
├─────────────────────────┼────────────┼────────┼─────────────────────┤
│ homepage.svg            │      0.982 │   ✓    │ Passed              │
│ login.svg               │      0.743 │   ✗    │ Below threshold     │
│ dashboard.svg           │        N/A │   ✗    │ File missing        │
└─────────────────────────┴────────────┴────────┴─────────────────────┘

✗ 2 of 3 comparisons failed
```

##### JSON Report Format

```json
{
  "threshold": 0.95,
  "summary": {
    "total": 3,
    "passed": 1,
    "failed": 2
  },
  "results": [
    {
      "baseline": "baselines/homepage.svg",
      "current": "current/homepage.svg",
      "similarity": 0.982,
      "passed": true
    }
  ]
}
```

#### Exit Codes

- `0` - All comparisons passed
- `1` - One or more comparisons failed or error occurred

---

### `migrate`

Migrate screenshots from other testing frameworks with automated discovery and conversion.

#### Usage

```bash
textual-snapshot migrate [OPTIONS]
```

#### Options

- `--from [pytest-textual-snapshot]` - Source format (default: pytest-textual-snapshot)
- `--dry-run` - Preview migration without making changes
- `--source-dir PATH` - Source directory (default: current directory)

#### Examples

##### Basic Migration

```bash
# Migrate from pytest-textual-snapshot
textual-snapshot migrate --from pytest-textual-snapshot

# Preview what will be migrated (safe)
textual-snapshot migrate --from pytest-textual-snapshot --dry-run

# Migrate from specific directory
textual-snapshot migrate --source-dir ./old-tests/
```

#### Migration Process

1. **Discovery**: Searches for pytest-textual-snapshot directories
2. **Planning**: Creates migration plan with file mappings
3. **Preview**: Shows what will be migrated (with `--dry-run`)
4. **Execution**: Copies files to textual-snapshots format
5. **Verification**: Reports migration results

#### Output

##### Migration Plan Preview

```
Migration Plan (DRY RUN)
┌─────────────────────────────────┬─────────────────────────────────┬─────────────┐
│ Source                          │ Target                          │ Size        │
├─────────────────────────────────┼─────────────────────────────────┼─────────────┤
│ test_snapshots/test_app.svg     │ screenshots/test_app_migrated_* │ 12,543 bytes│
│ snapshots/homepage.svg          │ screenshots/homepage_migrated_* │ 8,921 bytes │
└─────────────────────────────────┴─────────────────────────────────┴─────────────┘

DRY RUN: Would migrate 2 files
```

#### Migration Features

- ✅ **Safe**: Original files preserved
- ✅ **Automatic**: Finds pytest-textual-snapshot files automatically
- ✅ **Preview**: Dry-run mode shows exact changes
- ✅ **Timestamped**: New files get unique timestamps
- ✅ **Organized**: All migrated files go to `screenshots/` directory

---

### `convert`

Convert screenshots between SVG and PNG formats with quality control.

#### Usage

```bash
textual-snapshot convert INPUT_PATH --to FORMAT [OPTIONS]
```

#### Arguments

- `INPUT_PATH` - Input file or directory

#### Required Options

- `--to [png|svg]` - Target format for conversion

#### Options

- `--quality [low|medium|high]` - Quality for PNG output (default: high)
- `--output-dir, -o PATH` - Output directory (default: converted/)
- `--batch` - Process multiple files (required for directory input)

#### Examples

##### Single File Conversion

```bash
# SVG to PNG
textual-snapshot convert screenshot.svg --to png

# PNG to SVG
textual-snapshot convert screenshot.png --to svg

# High quality PNG
textual-snapshot convert screenshot.svg --to png --quality high
```

##### Batch Conversion

```bash
# Convert all SVG files to PNG
textual-snapshot convert screenshots/ --to png --batch

# Convert with custom output directory
textual-snapshot convert screenshots/ --to png --batch --output-dir ./png-exports/

# Lower quality for smaller files
textual-snapshot convert screenshots/ --to png --batch --quality medium
```

#### Quality Settings

| Quality  | DPI | Scale | Use Case                           |
| -------- | --- | ----- | ---------------------------------- |
| `low`    | 96  | 1.0x  | Quick previews, small file sizes   |
| `medium` | 144 | 1.5x  | Web display, balanced quality/size |
| `high`   | 192 | 2.0x  | High resolution, detailed captures |

#### Requirements

##### SVG to PNG

- **Requires**: Playwright and Chromium browser
- **Install**: `pip install playwright && playwright install chromium`
- **High-quality**: Browser-based rendering for perfect conversion

##### PNG to SVG

- **No additional requirements** (uses Python Pillow)
- **Note**: Creates SVG wrapper around embedded PNG data

#### Output

```
✓ Conversion completed successfully
Converted 5 files to /path/to/converted/
```

---

## Type Definitions

### Enums and Types

#### `ScreenshotFormat`

```python
from enum import Enum

class ScreenshotFormat(Enum):
    SVG = "svg"   # Vector format, smaller files, scalable
    PNG = "png"   # Raster format, broader tool support
    BOTH = "both" # Generate both SVG and PNG
```

#### `AppContext`

```python
from typing import Protocol

class AppContext(Protocol):
    """Protocol for app context information."""
    context: str
    format: ScreenshotFormat
    interactions: Optional[list[str]]
    output_dir: Path
```

### Type Hints and Imports

#### Complete Import Example

```python
from textual_snapshots import (
    # Main functions
    capture_app_screenshot,

    # Classes
    ScreenshotCapture,
    CaptureResult,

    # Enums
    ScreenshotFormat,

    # Plugin system
    CapturePlugin,

    # Type hints
    AppContext,
)

from textual.app import App
from pathlib import Path
from typing import Optional, Type
```

#### Type Annotations Example

```python
from textual_snapshots import capture_app_screenshot, CaptureResult, ScreenshotFormat
from textual.app import App
from pathlib import Path
from typing import Optional, Type

async def capture_with_types(
    app_class: Type[App],
    context: str,
    interactions: Optional[list[str]] = None,
    output_dir: Optional[Path] = None
) -> CaptureResult:
    """Type-annotated screenshot capture function."""
    result = await capture_app_screenshot(
        app_source=app_class,
        context=context,
        interactions=interactions,
        output_format=ScreenshotFormat.SVG,
        output_dir=output_dir
    )
    return result
```

## Error Handling

### Common Exceptions

```python
from textual_snapshots import capture_app_screenshot

try:
    result = await capture_app_screenshot(MyApp, context="test")
    if not result.success:
        print(f"Capture failed: {result.error_message}")
except ImportError as e:
    print(f"App import failed: {e}")
except FileNotFoundError as e:
    print(f"File not found: {e}")
except PermissionError as e:
    print(f"Permission denied: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Robust Error Handling Pattern

```python
async def robust_capture(app_class, context, max_retries=3):
    """Capture with retry logic and comprehensive error handling."""

    for attempt in range(max_retries):
        try:
            result = await capture_app_screenshot(app_class, context=context)

            if result.success:
                return result
            else:
                print(f"Attempt {attempt + 1} failed: {result.error_message}")

        except Exception as e:
            print(f"Attempt {attempt + 1} exception: {e}")

        if attempt < max_retries - 1:
            await asyncio.sleep(1.0)  # Wait before retry

    raise RuntimeError(f"Failed to capture screenshot after {max_retries} attempts")
```

## CLI Error Handling

### Common Exit Codes

- `0` - Success
- `1` - Command failed or user error
- `2` - Invalid command usage

### Common Errors

#### "No Textual applications found"

- **Cause**: No Textual apps in current directory
- **Solution**: Specify app file directly or use `--interactive`

#### "Format conversion not available"

- **Cause**: Unsupported format conversion requested
- **Solution**: Use SVG format (recommended) or check available formats

#### "Permission denied"

- **Cause**: Cannot write to output directory
- **Solution**: Check directory permissions or use `--output-dir`

### Verbose Mode

Use `--verbose` for detailed troubleshooting information:

```bash
textual-snapshot capture --verbose
# Shows app discovery process, file operations, timing
```

### Quiet Mode

Use `--quiet` for minimal output (CI/CD friendly):

```bash
textual-snapshot capture --quiet
# Only shows errors and final results
```

---

## Integration Examples

### GitHub Actions

```yaml
- name: Capture screenshots
  run: textual-snapshot capture tests/apps/ --batch --quiet

- name: Compare with baselines
  run: textual-snapshot compare baselines/ screenshots/ --output-report results.json
```

### Makefile

```makefile
screenshots:
	textual-snapshot capture --context "automated_test"

compare:
	textual-snapshot compare baselines/ screenshots/ --threshold 0.95

migrate:
	textual-snapshot migrate --from pytest-textual-snapshot --dry-run
```

### Shell Scripts

```bash
#!/bin/bash
# capture-all.sh
set -e

echo "Capturing all app screenshots..."
textual-snapshot capture app1.py --context "app1_main"
textual-snapshot capture app2.py --context "app2_main"
textual-snapshot capture app3.py --context "app3_main"

echo "Converting to PNG for web display..."
textual-snapshot convert screenshots/ --to png --batch --quality medium

echo "Done! Screenshots in screenshots/, PNGs in converted/"
```

---

**Complete API reference for textual-snapshots!** 📖 This covers all Python APIs and CLI commands for professional visual testing workflows.
