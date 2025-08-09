#!/usr/bin/env python3
"""
Basic Screenshot Capture Example

This example shows the simplest way to capture a screenshot of a Textual app.
Perfect for newcomers to understand the core concepts.
"""

import asyncio
import sys
from pathlib import Path

try:
    from textual.app import App, ComposeResult
    from textual.widgets import Button, Footer, Header, Static

    from textual_snapshots import ScreenshotFormat, capture_app_screenshot
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


class DemoApp(App):
    """A simple demo app for screenshot testing."""

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
    """

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Welcome to textual-snapshots!", id="welcome")
        yield Static("This is a demo app for testing screenshots.", id="description")
        yield Button("Click Me!", id="demo-button", variant="primary")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "demo-button":
            event.button.label = "Clicked! ✓"


async def main():
    """Demonstrate basic screenshot capture."""
    print("🎯 Basic Screenshot Capture Example")
    print("=" * 40)

    # Quick environment check
    try:
        # Test that we can instantiate the app
        DemoApp()
        print("✅ Textual app creation successful")
    except Exception as e:
        print(f"❌ Failed to create Textual app: {e}")
        return

    # 1. Basic capture (SVG format)
    print("\n1. Capturing basic app state (SVG format)...")
    result = await capture_app_screenshot(
        DemoApp,
        context="basic_demo"
    )

    if result.success:
        print(f"✅ SVG screenshot saved: {get_relative_path(result.screenshot_path)}")
        print(f"📏 File size: {result.file_size_bytes:,} bytes")
    else:
        print(f"❌ Capture failed: {result.error_message}")
        return

    # 2. Interactive capture (SVG format)
    print("\n2. Capturing after user interaction (SVG format)...")
    result = await capture_app_screenshot(
        DemoApp,
        context="button_clicked",
        interactions=[
            "click:#demo-button",  # Click the button
            "wait:0.5"             # Wait for any animations
        ],
        output_format=ScreenshotFormat.BOTH
    )

    if result.success:
        print(f"✅ Interactive SVG screenshot saved: {get_relative_path(result.screenshot_path)}")
        print(f"📏 File size: {result.file_size_bytes:,} bytes")
    else:
        print(f"❌ Interactive capture failed: {result.error_message}")
        return

    # 3. PNG format capture (requires Playwright)
    print("\n3. Capturing PNG format (requires Playwright)...")
    try:
        result_png = await capture_app_screenshot(
            DemoApp,
            context="png_demo",
            output_format=ScreenshotFormat.PNG
        )

        if result_png.success:
            print(f"✅ PNG screenshot saved: {get_relative_path(result_png.screenshot_path)}")
            print(f"📏 PNG file size: {result_png.file_size_bytes:,} bytes")
            if result_png.svg_path:
                print(f"📏 SVG file size: {result_png.svg_size_bytes:,} bytes")
                print(f"📊 Size comparison: SVG {result_png.svg_size_bytes:,} bytes → PNG {result_png.file_size_bytes:,} bytes")
        else:
            print(f"❌ PNG capture failed: {result_png.error_message}")

    except Exception as e:
        print(f"⚠️  PNG capture failed: {e}")
        print("💡 Install Playwright for PNG support: pip install playwright && playwright install chromium")

    # 4. BOTH format capture (creates both SVG and PNG)
    print("\n4. Capturing BOTH formats (SVG + PNG)...")
    try:
        result_both = await capture_app_screenshot(
            DemoApp,
            context="both_formats_demo",
            output_format=ScreenshotFormat.BOTH
        )

        if result_both.success:
            print("✅ Both formats captured successfully!")
            print(f"📄 SVG file: {get_relative_path(result_both.svg_path)} ({result_both.svg_size_bytes:,} bytes)")
            if result_both.png_path:
                print(f"🖼️  PNG file: {get_relative_path(result_both.png_path)} ({result_both.png_size_bytes:,} bytes)")
        else:
            print(f"❌ BOTH format capture failed: {result_both.error_message}")

    except Exception as e:
        print(f"⚠️  BOTH format capture failed: {e}")

    # 5. Show results
    screenshots_dir = Path("screenshots")
    if screenshots_dir.exists():
        # Find all screenshot files recursively
        svg_screenshots = list(screenshots_dir.rglob("*.svg"))
        png_screenshots = list(screenshots_dir.rglob("*.png"))

        print("\n📁 Screenshots captured:")
        print(f"  • SVG files: {len(svg_screenshots)}")
        print(f"  • PNG files: {len(png_screenshots)}")

        print("\n📂 Screenshot locations:")
        for screenshot in sorted(svg_screenshots + png_screenshots):
            size = screenshot.stat().st_size
            format_icon = "📄" if screenshot.suffix == ".svg" else "🖼️"
            print(f"  {format_icon} {get_relative_path(screenshot)} ({size:,} bytes)")

        print("\n🎉 Success! Screenshots saved to the locations above.")
        print("\n💡 Tips:")
        print("  • Open .svg files in your browser to view them")
        print("  • .png files can be opened in any image viewer")
        print("  • SVG files are smaller and scalable")
        print("  • PNG files work better for sharing/embedding")
        print("  • Use ScreenshotFormat.BOTH to get both formats at once")

    print("\n" + "=" * 40)
    print("Example completed! 🚀")


if __name__ == "__main__":
    asyncio.run(main())
