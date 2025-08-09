#!/usr/bin/env python3
"""
Plugin Development Example

This example shows how to create custom plugins for textual-snapshots.
Great for understanding the plugin architecture and extending functionality.

Demonstrates:
- Custom logging and metrics collection
- Screenshot validation and quality checks
- Error handling and recovery
- Plugin composition and ordering
"""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

try:
    from textual.app import App, ComposeResult
    from textual.widgets import Button, Footer, Header, Static

    from textual_snapshots import CaptureResult, ScreenshotFormat, capture_app_screenshot
    from textual_snapshots.plugins import BasePlugin
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure you've installed the package: pip install -e .")
    sys.exit(1)


def get_relative_path(path: Path) -> str:
    """Convert absolute path to relative path from current working directory."""
    try:
        rel_path = path.relative_to(Path.cwd())
        # If the path is too deep, show a more readable version
        parts = rel_path.parts
        if len(parts) > 4:
            # Show screenshots/.../context/filename for very deep paths
            return f"screenshots/.../{parts[-2]}/{parts[-1]}"
        else:
            return str(rel_path)
    except ValueError:
        # If path is not relative to cwd, show a meaningful fallback
        return f"screenshots/{path.parent.name}/{path.name}"


class PluginDemoApp(App):
    """Demo app for plugin demonstration with interactive elements."""

    CSS = """
    Static {
        text-align: center;
        margin: 1;
        padding: 1;
        background: $primary;
        color: $text;
    }
    
    Button {
        margin: 1;
    }
    
    #status {
        background: $success;
        color: $text;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.click_count = 0

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("🔌 Plugin Development Demo", id="title")
        yield Static("This app demonstrates custom plugins in action.", id="description")
        yield Button("Click Me!", id="demo-button", variant="primary")
        yield Static(f"Clicks: {self.click_count}", id="status")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "demo-button":
            self.click_count += 1
            self.query_one("#status", Static).update(f"Clicks: {self.click_count}")
            if self.click_count >= 3:
                event.button.label = "Max Clicks Reached!"
                event.button.disabled = True


class DetailedLoggingPlugin(BasePlugin):
    """Plugin that provides comprehensive logging with timing and context."""

    def __init__(self, logger_name: str = "textual_snapshots.plugin_demo", log_level: str = "INFO"):
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        self.start_time = None
        self.capture_count = 0

    async def pre_capture(self, context: str, app_context):
        """Called before screenshot capture."""
        self.capture_count += 1
        self.start_time = datetime.now()

        self.logger.info(f"🚀 \033[1m\033[96mStarting capture #{self.capture_count}\033[0m: \033[93m{context}\033[0m")
        self.logger.debug(f"📱 App: \033[95m{app_context.context_name}\033[0m")
        self.logger.debug(f"🕐 Start time: \033[90m{self.start_time.strftime('%H:%M:%S.%f')[:-3]}\033[0m")

        return {"start_time": self.start_time, "capture_number": self.capture_count}

    async def post_capture(self, result: CaptureResult, metadata):
        """Called after successful capture."""
        start_time = metadata.get("start_time", self.start_time)
        capture_num = metadata.get("capture_number", self.capture_count)
        duration = (datetime.now() - start_time).total_seconds() if start_time else 0

        self.logger.info(
            f"✅ \033[1m\033[92mCapture #{capture_num} completed\033[0m: \033[94m{get_relative_path(result.screenshot_path)}\033[0m "
            f"(\033[96m{result.file_size_bytes:,} bytes\033[0m, \033[91m{duration:.2f}s\033[0m)"
        )

        # Log format-specific details
        if result.png_path:
            self.logger.debug(f"🖼️  PNG: \033[94m{get_relative_path(result.png_path)}\033[0m (\033[96m{result.png_size_bytes:,} bytes\033[0m)")
        if result.svg_path:
            self.logger.debug(f"📄 SVG: \033[94m{get_relative_path(result.svg_path)}\033[0m (\033[96m{result.svg_size_bytes:,} bytes\033[0m)")

    async def on_failure(self, error: Exception, context: str):
        """Called if capture fails."""
        duration = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        self.logger.error(f"❌ \033[1m\033[91mCapture failed\033[0m after \033[91m{duration:.2f}s\033[0m: \033[93m{error}\033[0m")
        self.logger.debug(f"💥 Error type: \033[95m{type(error).__name__}\033[0m")
        self.logger.debug(f"📍 Context: \033[93m{context}\033[0m")


class QualityValidationPlugin(BasePlugin):
    """Plugin that validates screenshot quality, format, and content."""

    def __init__(self, min_size_bytes: int = 1000, max_size_bytes: int = 10 * 1024 * 1024, strict_mode: bool = False):
        self.min_size = min_size_bytes
        self.max_size = max_size_bytes
        self.strict_mode = strict_mode
        self.validation_results = []

    async def pre_capture(self, context: str, app_context):
        """Pre-capture validation setup."""
        return {"validation_context": context}

    async def post_capture(self, result: CaptureResult, metadata):
        """Comprehensive screenshot validation."""
        validation_result = {
            "context": metadata.get("validation_context", "unknown"),
            "timestamp": datetime.now(),
            "passed": True,
            "warnings": [],
            "errors": []
        }

        try:
            # File existence validation
            if not result.screenshot_path or not result.screenshot_path.exists():
                validation_result["errors"].append("Screenshot file not found")
                validation_result["passed"] = False
                raise FileNotFoundError(f"Screenshot file not found: {result.screenshot_path}")

            # Size validation
            size = result.file_size_bytes
            if size < self.min_size:
                error_msg = f"Screenshot too small ({size:,} bytes) - minimum: {self.min_size:,} bytes"
                validation_result["errors"].append(error_msg)
                validation_result["passed"] = False
                if self.strict_mode:
                    raise ValueError(error_msg)

            if size > self.max_size:
                warning_msg = f"Large screenshot ({size:,} bytes) - maximum recommended: {self.max_size:,} bytes"
                validation_result["warnings"].append(warning_msg)
                print(f"⚠️  \033[93m{warning_msg}\033[0m")

            # Format-specific validation
            if result.screenshot_path.suffix == '.svg':
                self._validate_svg_content(result.screenshot_path, validation_result)
            elif result.screenshot_path.suffix == '.png':
                self._validate_png_content(result.screenshot_path, validation_result)

            # Multi-format validation
            if result.svg_path and result.png_path:
                self._validate_format_consistency(result, validation_result)

            if validation_result["passed"]:
                print(f"✅ \033[1m\033[92mValidation passed\033[0m: \033[94m{get_relative_path(result.screenshot_path)}\033[0m")
                if validation_result["warnings"]:
                    print(f"   ⚠️  \033[93m{len(validation_result['warnings'])} warnings\033[0m")
            else:
                print(f"❌ \033[1m\033[91mValidation failed\033[0m: \033[91m{len(validation_result['errors'])} errors\033[0m")

        finally:
            self.validation_results.append(validation_result)

    def _validate_svg_content(self, svg_path: Path, validation_result: dict):
        """Validate SVG file content and structure."""
        try:
            content = svg_path.read_text(encoding='utf-8')

            # Check SVG format
            if not (content.strip().startswith('<?xml') or content.strip().startswith('<svg')):
                validation_result["errors"].append("Invalid SVG format - missing XML declaration or SVG tag")
                validation_result["passed"] = False

            # Check for viewBox (important for proper scaling)
            if 'viewBox=' not in content:
                validation_result["warnings"].append("SVG missing viewBox attribute - may not scale properly")

            # Check for content (should have some visual elements)
            if content.count('<') < 5:  # Very basic content check
                validation_result["warnings"].append("SVG appears to have minimal content")

        except UnicodeDecodeError:
            validation_result["errors"].append("SVG file encoding error")
            validation_result["passed"] = False

    def _validate_png_content(self, png_path: Path, validation_result: dict):
        """Validate PNG file content."""
        try:
            # Check PNG header
            with open(png_path, 'rb') as f:
                header = f.read(8)
                if header != b'\x89PNG\r\n\x1a\n':
                    validation_result["errors"].append("Invalid PNG file header")
                    validation_result["passed"] = False
        except Exception as e:
            validation_result["errors"].append(f"PNG validation error: {e}")
            validation_result["passed"] = False

    def _validate_format_consistency(self, result: CaptureResult, validation_result: dict):
        """Validate consistency between SVG and PNG formats."""
        svg_size = result.svg_size_bytes
        png_size = result.png_size_bytes

        # PNG should generally be larger than SVG for the same content
        if png_size < svg_size:
            validation_result["warnings"].append(
                f"PNG ({png_size:,} bytes) smaller than SVG ({svg_size:,} bytes) - unusual"
            )

    def get_validation_summary(self) -> dict:
        """Get summary of all validations performed."""
        total = len(self.validation_results)
        passed = sum(1 for r in self.validation_results if r["passed"])
        total_warnings = sum(len(r["warnings"]) for r in self.validation_results)
        total_errors = sum(len(r["errors"]) for r in self.validation_results)

        return {
            "total_validations": total,
            "passed": passed,
            "failed": total - passed,
            "success_rate": (passed / total * 100) if total > 0 else 0,
            "total_warnings": total_warnings,
            "total_errors": total_errors
        }

    async def on_failure(self, error: Exception, context: str):
        """Handle validation failures."""
        validation_result = {
            "context": context,
            "timestamp": datetime.now(),
            "passed": False,
            "warnings": [],
            "errors": [f"Capture failed: {str(error)}"]
        }
        self.validation_results.append(validation_result)


class PerformanceMetricsPlugin(BasePlugin):
    """Plugin that collects detailed performance and usage metrics."""

    def __init__(self):
        self.metrics = {
            'total_captures': 0,
            'successful_captures': 0,
            'failed_captures': 0,
            'total_svg_size': 0,
            'total_png_size': 0,
            'formats_used': {'svg': 0, 'png': 0, 'both': 0}
        }
        self.durations = []
        self.contexts = []
        self.start_time = None
        self.detailed_results = []

    async def pre_capture(self, context: str, app_context):
        """Start timing and record context."""
        self.start_time = datetime.now()
        self.metrics['total_captures'] += 1
        self.contexts.append(context)

        # Show that metrics plugin is active
        print(f"📊 \033[90mMetrics plugin: Starting timer for capture #{self.metrics['total_captures']}\033[0m")

        return {"metrics_start_time": self.start_time}

    async def post_capture(self, result: CaptureResult, metadata):
        """Record detailed capture metrics."""
        start_time = metadata.get("metrics_start_time", self.start_time)
        duration = (datetime.now() - start_time).total_seconds() if start_time else 0
        self.durations.append(duration)

        self.metrics['successful_captures'] += 1

        # Track format usage and sizes
        if result.svg_path:
            self.metrics['total_svg_size'] += result.svg_size_bytes
        if result.png_path:
            self.metrics['total_png_size'] += result.png_size_bytes

        # Track format combinations based on requested format, not file existence
        if result.format == ScreenshotFormat.BOTH:
            self.metrics['formats_used']['both'] += 1
            format_desc = "Both SVG+PNG"
        elif result.format == ScreenshotFormat.PNG:
            self.metrics['formats_used']['png'] += 1
            format_desc = "PNG only"
        else:  # SVG format
            self.metrics['formats_used']['svg'] += 1
            format_desc = "SVG only"

        # Store detailed result
        self.detailed_results.append({
            'context': result.context,
            'duration': duration,
            'svg_size': result.svg_size_bytes,
            'png_size': result.png_size_bytes,
            'format': result.format,
            'timestamp': datetime.now()
        })

        # Show immediate metrics feedback
        total_captures = self.metrics['total_captures']
        success_rate = (self.metrics['successful_captures'] / total_captures * 100) if total_captures > 0 else 0
        avg_duration = sum(self.durations) / len(self.durations) if self.durations else 0

        print(f"📊 \033[1m\033[94mMetrics\033[0m: \033[96m{format_desc}\033[0m, "
              f"\033[95m{duration:.2f}s\033[0m, "
              f"\033[92m{success_rate:.0f}% success rate\033[0m "
              f"(\033[90m{self.metrics['successful_captures']}/{total_captures}\033[0m), "
              f"\033[93mavg {avg_duration:.2f}s\033[0m")

    async def on_failure(self, error: Exception, context: str):
        """Record failed capture."""
        self.metrics['failed_captures'] += 1
        duration = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        self.durations.append(duration)  # Include failed attempts in timing

    def print_detailed_summary(self):
        """Print comprehensive metrics summary."""
        print("\n📊 Performance Metrics Summary")
        print("=" * 50)

        # Basic stats
        total = self.metrics['total_captures']
        successful = self.metrics['successful_captures']
        failed = self.metrics['failed_captures']

        print("📈 Capture Statistics:")
        print(f"  • Total attempts: {total}")
        print(f"  • Successful: {successful}")
        print(f"  • Failed: {failed}")
        print(f"  • Success rate: {(successful / max(1, total) * 100):.1f}%")

        # Timing stats
        if self.durations:
            avg_duration = sum(self.durations) / len(self.durations)
            min_duration = min(self.durations)
            max_duration = max(self.durations)

            print("\n⏱️  Timing Statistics:")
            print(f"  • Average duration: {avg_duration:.2f}s")
            print(f"  • Fastest capture: {min_duration:.2f}s")
            print(f"  • Slowest capture: {max_duration:.2f}s")
            print(f"  • Total time: {sum(self.durations):.2f}s")

        # Format usage
        formats = self.metrics['formats_used']
        print("\n📄 Format Usage:")
        print(f"  • SVG only: {formats['svg']}")
        print(f"  • PNG only: {formats['png']}")
        print(f"  • Both formats: {formats['both']}")

        # Size statistics
        total_svg = self.metrics['total_svg_size']
        total_png = self.metrics['total_png_size']

        if total_svg > 0 or total_png > 0:
            print("\n💾 Size Statistics:")
            if total_svg > 0:
                avg_svg = total_svg / max(1, formats['svg'] + formats['both'])
                print(f"  • Total SVG size: {total_svg:,} bytes")
                print(f"  • Average SVG size: {avg_svg:,.0f} bytes")
            if total_png > 0:
                avg_png = total_png / max(1, formats['png'] + formats['both'])
                print(f"  • Total PNG size: {total_png:,} bytes")
                print(f"  • Average PNG size: {avg_png:,.0f} bytes")

        # Context analysis
        if self.contexts:
            unique_contexts = len(set(self.contexts))
            print("\n🏷️  Context Analysis:")
            print(f"  • Unique contexts: {unique_contexts}")
            print(f"  • Most common: {max(set(self.contexts), key=self.contexts.count)}")

    def get_metrics_dict(self) -> dict:
        """Get metrics as a dictionary for programmatic use."""
        return {
            **self.metrics,
            'average_duration': sum(self.durations) / len(self.durations) if self.durations else 0,
            'min_duration': min(self.durations) if self.durations else 0,
            'max_duration': max(self.durations) if self.durations else 0,
            'unique_contexts': len(set(self.contexts)),
            'detailed_results': self.detailed_results
        }


async def main():
    """Demonstrate comprehensive plugin usage with multiple scenarios."""
    print("\033[1m\033[96m🔌 Plugin Development Example\033[0m")
    print("\033[94m" + "=" * 60 + "\033[0m")

    # Setup colorful logging with custom format
    class ColoredFormatter(logging.Formatter):
        """Custom formatter with colors for different log levels."""

        # ANSI color codes
        COLORS = {
            'DEBUG': '\033[36m',    # Cyan
            'INFO': '\033[32m',     # Green
            'WARNING': '\033[33m',  # Yellow
            'ERROR': '\033[31m',    # Red
            'CRITICAL': '\033[35m', # Magenta
        }
        RESET = '\033[0m'
        BOLD = '\033[1m'

        def format(self, record):
            # Add color to log level
            level_color = self.COLORS.get(record.levelname, '')
            record.levelname = f"{level_color}{self.BOLD}{record.levelname}{self.RESET}"

            # Add color to logger name
            if 'plugin_demo' in record.name:
                record.name = f"\033[94m{self.BOLD}🔌 {record.name.split('.')[-1]}{self.RESET}"

            # Format the message
            formatted = super().format(record)
            return formatted

    # Configure logging with colors
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create colored console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    colored_formatter = ColoredFormatter(
        fmt='%(asctime)s │ %(name)s │ %(levelname)s │ %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(colored_formatter)
    logger.addHandler(console_handler)

    # Create plugins with different configurations
    logging_plugin = DetailedLoggingPlugin(log_level="INFO")
    validation_plugin = QualityValidationPlugin(
        min_size_bytes=500,
        max_size_bytes=5 * 1024 * 1024,
        strict_mode=False  # Allow warnings without failing
    )
    metrics_plugin = PerformanceMetricsPlugin()

    print("\n\033[1m\033[93m🎯 Demonstrating plugin capabilities...\033[0m")
    print("   \033[90mFor each capture, plugins run in order: \033[92mLogging\033[90m → \033[93mValidation\033[90m → \033[94mMetrics\033[0m")
    print("   \033[90mMetrics summary will be shown after all captures complete\033[0m")

    # Test scenarios with different formats and interactions
    test_scenarios = [
        {
            "name": "basic_state",
            "description": "Basic app state (SVG)",
            "format": ScreenshotFormat.SVG,
            "interactions": None
        },
        {
            "name": "interactive_state",
            "description": "After user interaction (PNG)",
            "format": ScreenshotFormat.PNG,
            "interactions": ["click:#demo-button", "wait:0.5"]
        },
        {
            "name": "multi_click_state",
            "description": "Multiple interactions (Both formats)",
            "format": ScreenshotFormat.BOTH,
            "interactions": [
                "click:#demo-button", "wait:0.3",
                "click:#demo-button", "wait:0.3",
                "click:#demo-button", "wait:0.5"
            ]
        }
    ]

    print(f"\n\033[1m\033[95m📋 Running {len(test_scenarios)} test scenarios...\033[0m")

    # Define plugins to use for all scenarios
    plugins = [
        logging_plugin,      # First: logs everything
        validation_plugin,   # Second: validates quality
        metrics_plugin       # Third: collects metrics
    ]

    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n\033[1m\033[96m--- Scenario {i}: {scenario['description']} ---\033[0m")

        try:
            # Use the simple capture_app_screenshot function with plugins
            result = await capture_app_screenshot(
                PluginDemoApp,
                context=f"plugin_demo_{scenario['name']}",
                output_format=scenario['format'],
                interactions=scenario['interactions'],
                metadata={"scenario": scenario['name'], "test_run": True},
                plugins=plugins
            )

            if result.success:
                print(f"✅ \033[1m\033[92mScenario {i} completed successfully\033[0m")
                # Show what was created
                if result.svg_path:
                    print(f"   📄 SVG: \033[94m{get_relative_path(result.svg_path)}\033[0m")
                if result.png_path:
                    print(f"   🖼️  PNG: \033[94m{get_relative_path(result.png_path)}\033[0m")
            else:
                print(f"❌ \033[1m\033[91mScenario {i} failed\033[0m: \033[93m{result.error_message}\033[0m")

        except Exception as e:
            print(f"💥 \033[1m\033[91mScenario {i} crashed\033[0m: \033[93m{e}\033[0m")

    # Show comprehensive results
    print("\n" + "\033[94m" + "=" * 60 + "\033[0m")
    print("\033[1m\033[96m📊 PLUGIN RESULTS SUMMARY\033[0m")
    print("\033[90mNote: Plugins ran in order for each capture. This is the final aggregated data.\033[0m")
    print("\033[94m" + "=" * 60 + "\033[0m")

    # Metrics summary
    metrics_plugin.print_detailed_summary()

    # Validation summary
    validation_summary = validation_plugin.get_validation_summary()
    print("\n🔍 Validation Summary:")
    print(f"  • Total validations: {validation_summary['total_validations']}")
    print(f"  • Passed: {validation_summary['passed']}")
    print(f"  • Failed: {validation_summary['failed']}")
    print(f"  • Success rate: {validation_summary['success_rate']:.1f}%")
    print(f"  • Total warnings: {validation_summary['total_warnings']}")
    print(f"  • Total errors: {validation_summary['total_errors']}")

    # Show created files
    screenshots_dir = Path("screenshots")
    if screenshots_dir.exists():
        svg_files = list(screenshots_dir.rglob("plugin_demo_*.svg"))
        png_files = list(screenshots_dir.rglob("plugin_demo_*.png"))

        if svg_files or png_files:
            print("\n📁 Created Files:")
            for file_path in sorted(svg_files + png_files):
                size = file_path.stat().st_size
                format_icon = "📄" if file_path.suffix == ".svg" else "🖼️"
                print(f"  {format_icon} {get_relative_path(file_path)} ({size:,} bytes)")

    print("\n💡 Plugin Development Tips:")
    print("  • Plugins run in the order they're added to the list")
    print("  • Use pre_capture() for setup, validation, and preparation")
    print("  • Use post_capture() for processing, analysis, and cleanup")
    print("  • Use on_failure() for error handling and recovery")
    print("  • Return metadata from pre_capture() to pass data to post_capture()")
    print("  • Exceptions in plugins will stop the entire capture process")
    print("  • Inherit from BasePlugin for default implementations")

    print("\n🚀 Plugin Architecture Benefits:")
    print("  • Modular and reusable components")
    print("  • Easy to test individual plugin functionality")
    print("  • Composable - mix and match plugins as needed")
    print("  • Extensible - add custom logic without modifying core code")

    print("\n" + "\033[94m" + "=" * 60 + "\033[0m")
    print("\033[1m\033[92mPlugin development example completed! 🎉\033[0m")


if __name__ == "__main__":
    asyncio.run(main())
