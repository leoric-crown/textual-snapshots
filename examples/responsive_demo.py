#!/usr/bin/env python3
"""
Responsive Screenshot Demo

This example demonstrates capturing screenshots at different terminal sizes
and quality settings. Perfect for testing responsive layouts and creating
documentation for various screen sizes.

Features:
- Multiple terminal sizes (mobile, tablet, desktop, ultrawide)
- Different quality settings for PNG output
- Responsive layout testing
- Batch processing with organized output
"""

import asyncio
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
    from textual.app import App, ComposeResult
    from textual.containers import Container
    from textual.widgets import Footer, Header, Static, TabPane, Tabs

    from textual_snapshots import ScreenshotFormat, capture_app_screenshot
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure you've installed the package: pip install -e .")
    if "PIL" in str(e):
        print("💡 For image stitching, install Pillow: pip install Pillow")
    sys.exit(1)


def get_relative_path(path: Path) -> str:
    """Convert absolute path to relative path from current working directory."""
    try:
        rel_path = path.relative_to(Path.cwd())
        parts = rel_path.parts
        if len(parts) > 4:
            return f"screenshots/.../{parts[-2]}/{parts[-1]}"
        else:
            return str(rel_path)
    except ValueError:
        return f"screenshots/{path.parent.name}/{path.name}"


class ResponsiveApp(App):
    """Demo app that showcases responsive design at different screen sizes."""

    # Responsive breakpoints - Textual will automatically apply CSS classes
    HORIZONTAL_BREAKPOINTS = [
        (0, "-narrow"),      # 0-50 chars: narrow terminal
        (51, "-compact"),    # 51-80 chars: compact terminal
        (81, "-standard"),   # 81-120 chars: standard terminal
        (121, "-wide"),      # 121+ chars: wide terminal
    ]

    CSS = """
    /* Base styles */
    .header-section {
        background: $primary;
        color: $text;
        text-align: center;
        padding: 1;
        margin-bottom: 1;
    }

    .content-grid {
        layout: grid;
        grid-size: 2 2;
        grid-gutter: 1;
        margin: 1;
    }

    .card {
        background: $surface;
        border: solid $primary;
        padding: 1;
        text-align: center;
    }

    .stats-container {
        layout: horizontal;
        margin: 1;
    }

    .stat-box {
        background: $success;
        color: $text;
        text-align: center;
        padding: 1;
        margin: 0 1;
        min-width: 15;
    }

    .footer-info {
        background: $warning;
        color: $text;
        text-align: center;
        padding: 1;
    }

    /* Narrow terminal styles (0-50 chars) */
    .-narrow .header-section {
        padding: 0;
    }

    .-narrow .content-grid {
        grid-size: 1 4;
    }

    .-narrow .card {
        padding: 0;
    }

    .-narrow .stats-container {
        layout: vertical;
    }

    .-narrow .stat-box {
        margin: 1 0;
    }

    /* Compact terminal styles (51-80 chars) */
    .-compact .content-grid {
        grid-size: 1 4;
    }

    .-compact .stats-container {
        layout: vertical;
    }

    .-compact .stat-box {
        margin: 1 0;
    }

    /* Standard terminal styles (81-120 chars) */
    .-standard .content-grid {
        grid-size: 2 2;
    }

    /* Wide terminal styles (121+ chars) - enhanced layouts */
    .-wide .content-grid {
        grid-size: 4 1;
    }

    .-wide .stats-container {
        layout: horizontal;
    }
    """

    def __init__(self, size_name: str = "default", **kwargs):
        super().__init__(**kwargs)
        self.size_name = size_name

    def compose(self) -> ComposeResult:
        yield Header()

        yield Static(
            f"🖥️ TUI Responsive Demo - {self.size_name.replace('_', ' ').title()}",
            classes="header-section",
            id="main-header"
        )

        with Container(classes="content-grid"):
            yield Static("🏠 Dashboard", classes="card", id="dashboard")
            yield Static("📊 Analytics", classes="card", id="analytics")
            yield Static("⚙️ Settings", classes="card", id="settings")
            yield Static("👤 Profile", classes="card", id="profile")

        with Container(classes="stats-container"):
            yield Static("Users\n1,234", classes="stat-box", id="users")
            yield Static("Revenue\n$56,789", classes="stat-box", id="revenue")
            yield Static("Growth\n+12.5%", classes="stat-box", id="growth")

        with Tabs():
            with TabPane("Overview", id="overview"):
                yield Static("📈 Key metrics and performance indicators", id="overview-content")
            with TabPane("Details", id="details"):
                yield Static("🔍 Detailed breakdown and analysis", id="details-content")
            with TabPane("Reports", id="reports"):
                yield Static("📋 Generated reports and exports", id="reports-content")

        yield Static(
            f"Terminal Size: {self.size_name.replace('_', ' ').title()} | Responsive Layout Active",
            classes="footer-info",
            id="size-indicator"
        )

        yield Footer()


# Terminal size configurations for different TUI breakpoints
TERMINAL_SIZES = {
    "narrow": {
        "size": (50, 20),
        "description": "Narrow terminal window",
        "use_case": "Small terminal, SSH sessions"
    },
    "compact": {
        "size": (80, 24),
        "description": "Compact terminal layout",
        "use_case": "Standard terminal, tmux panes"
    },
    "standard": {
        "size": (120, 30),
        "description": "Standard terminal window",
        "use_case": "Full terminal, IDE integrated"
    },
    "wide": {
        "size": (160, 35),
        "description": "Wide terminal layout",
        "use_case": "Large monitors, side-by-side"
    }
}

# Quality settings for PNG output
QUALITY_SETTINGS = {
    "low": {
        "description": "Low quality (72 DPI)",
        "use_case": "Quick previews, web thumbnails"
    },
    "medium": {
        "description": "Medium quality (144 DPI)",
        "use_case": "Web display, documentation"
    },
    "high": {
        "description": "High quality (192 DPI)",
        "use_case": "Print, high-res documentation"
    }
}


async def capture_responsive_screenshots():
    """Capture screenshots at different terminal sizes."""
    print("📱 \033[1m\033[96mResponsive Screenshot Demo\033[0m")
    print("\033[94m" + "=" * 60 + "\033[0m")

    print("\n🎯 \033[1m\033[93mCapturing at different terminal sizes...\033[0m")
    print(f"   \033[90mTesting {len(TERMINAL_SIZES)} different screen sizes\033[0m")

    results = []

    for size_name, config in TERMINAL_SIZES.items():
        width, height = config["size"]
        print(f"\n\033[1m\033[96m--- {size_name.replace('_', ' ').title()} ({width}x{height}) ---\033[0m")
        print(f"   \033[90m{config['description']} - {config['use_case']}\033[0m")

        try:
            # Capture SVG with specific terminal size
            result_svg = await capture_app_screenshot(
                ResponsiveApp(size_name=size_name),
                context=f"responsive_{size_name}_svg",
                output_format=ScreenshotFormat.SVG,
                metadata={"terminal_size": config["size"]}
            )

            if result_svg.success:
                print(f"   📄 SVG: \033[94m{get_relative_path(result_svg.screenshot_path)}\033[0m "
                      f"(\033[96m{result_svg.file_size_bytes:,} bytes\033[0m)")
                results.append(("SVG", size_name, result_svg))
            else:
                print(f"   ❌ SVG capture failed: {result_svg.error_message}")

        except Exception as e:
            print(f"   💥 \033[91mFailed to capture {size_name}\033[0m: {e}")

    return results


async def capture_quality_comparison():
    """Demonstrate different PNG quality settings."""
    print("\n🎨 \033[1m\033[93mPNG Quality Comparison\033[0m")
    print(f"   \033[90mTesting {len(QUALITY_SETTINGS)} quality levels on desktop size\033[0m")

    quality_results = []

    for quality, config in QUALITY_SETTINGS.items():
        print(f"\n\033[1m\033[95m--- {quality.title()} Quality ---\033[0m")
        print(f"   \033[90m{config['description']} - {config['use_case']}\033[0m")

        try:
            # Note: We can't directly control PNG quality through the capture API yet
            # This would require extending the conversion system
            result = await capture_app_screenshot(
                ResponsiveApp(size_name=f"desktop_{quality}_quality"),
                context=f"quality_demo_{quality}",
                output_format=ScreenshotFormat.PNG,
                metadata={"terminal_size": (120, 30)}  # Desktop size for quality comparison
            )

            if result.success:
                print(f"   🖼️  PNG: \033[94m{get_relative_path(result.screenshot_path)}\033[0m "
                      f"(\033[96m{result.file_size_bytes:,} bytes\033[0m)")
                quality_results.append((quality, result))
            else:
                print(f"   ❌ PNG capture failed: {result.error_message}")

        except Exception as e:
            print(f"   💥 \033[91mFailed to capture {quality} quality\033[0m: {e}")

    return quality_results


async def capture_format_comparison():
    """Compare SVG vs PNG formats at the same size."""
    print("\n📊 \033[1m\033[93mFormat Comparison (Desktop Size)\033[0m")
    print("   \033[90mComparing SVG vs PNG vs Both formats\033[0m")

    format_results = []
    formats = [
        ("svg_only", ScreenshotFormat.SVG, "SVG vector format"),
        ("png_only", ScreenshotFormat.PNG, "PNG raster format"),
        ("both_formats", ScreenshotFormat.BOTH, "Both SVG and PNG")
    ]

    for format_name, format_type, description in formats:
        print(f"\n\033[1m\033[94m--- {description} ---\033[0m")

        try:
            result = await capture_app_screenshot(
                ResponsiveApp(size_name="desktop_comparison"),
                context=f"format_comparison_{format_name}",
                output_format=format_type,
                metadata={"terminal_size": (120, 30)}  # Desktop size for format comparison
            )

            if result.success:
                print("   ✅ \033[92mCapture successful\033[0m")
                if result.svg_path:
                    print(f"   📄 SVG: \033[94m{get_relative_path(result.svg_path)}\033[0m "
                          f"(\033[96m{result.svg_size_bytes:,} bytes\033[0m)")
                if result.png_path:
                    print(f"   🖼️  PNG: \033[94m{get_relative_path(result.png_path)}\033[0m "
                          f"(\033[96m{result.png_size_bytes:,} bytes\033[0m)")

                format_results.append((format_name, result))
            else:
                print(f"   ❌ Capture failed: {result.error_message}")

        except Exception as e:
            print(f"   💥 \033[91mFailed to capture {format_name}\033[0m: {e}")

    return format_results


def print_summary(responsive_results: list, quality_results: list, format_results: list, composite_path: Path = None):
    """Print comprehensive summary of all captures."""
    print("\n" + "\033[94m" + "=" * 60 + "\033[0m")
    print("\033[1m\033[96m📊 RESPONSIVE CAPTURE SUMMARY\033[0m")
    print("\033[94m" + "=" * 60 + "\033[0m")

    # Responsive sizes summary
    if responsive_results:
        print(f"\n📱 \033[1m\033[93mResponsive Sizes Captured: {len(responsive_results)}\033[0m")
        total_size = 0
        for _format_type, size_name, result in responsive_results:
            size_config = TERMINAL_SIZES[size_name]
            width, height = size_config["size"]
            file_size = result.file_size_bytes
            total_size += file_size

            print(f"  • \033[95m{size_name.replace('_', ' ').title()}\033[0m "
                  f"({width}x{height}): \033[96m{file_size:,} bytes\033[0m")

        print(f"  \033[90mTotal responsive captures: {total_size:,} bytes\033[0m")

    # Quality comparison summary
    if quality_results:
        print("\n🎨 \033[1m\033[93mQuality Comparison:\033[0m")
        for quality, result in quality_results:
            print(f"  • \033[95m{quality.title()}\033[0m quality: "
                  f"\033[96m{result.file_size_bytes:,} bytes\033[0m")

    # Format comparison summary
    if format_results:
        print("\n📊 \033[1m\033[93mFormat Comparison:\033[0m")
        for format_name, result in format_results:
            format_desc = format_name.replace('_', ' ').title()
            if result.svg_path and result.png_path:
                total_size = result.svg_size_bytes + result.png_size_bytes
                print(f"  • \033[95m{format_desc}\033[0m: "
                      f"SVG \033[96m{result.svg_size_bytes:,}B\033[0m + "
                      f"PNG \033[96m{result.png_size_bytes:,}B\033[0m = "
                      f"\033[93m{total_size:,}B total\033[0m")
            elif result.png_path:
                print(f"  • \033[95m{format_desc}\033[0m: "
                      f"\033[96m{result.png_size_bytes:,} bytes\033[0m")
            else:
                print(f"  • \033[95m{format_desc}\033[0m: "
                      f"\033[96m{result.svg_size_bytes:,} bytes\033[0m")

    # Show composite image if created
    if composite_path and composite_path.exists():
        composite_size = composite_path.stat().st_size
        print("\n🎨 \033[1m\033[93mResponsive Composite Image:\033[0m")
        print(f"  🖼️  \033[94m{get_relative_path(composite_path)}\033[0m "
              f"(\033[96m{composite_size:,} bytes\033[0m)")
        print("  🖥️ Shows narrow, compact, standard, and wide terminal layouts side by side")

    # Show all created files
    screenshots_dir = Path("screenshots")
    if screenshots_dir.exists():
        svg_files = list(screenshots_dir.rglob("responsive_*.svg")) + list(screenshots_dir.rglob("quality_*.svg")) + list(screenshots_dir.rglob("format_*.svg"))
        png_files = list(screenshots_dir.rglob("responsive_*.png")) + list(screenshots_dir.rglob("quality_*.png")) + list(screenshots_dir.rglob("format_*.png")) + list(screenshots_dir.rglob("composite_*.png"))
        composite_files = list(screenshots_dir.rglob("tui_responsive_composite.png"))

        all_files = svg_files + png_files + composite_files
        if all_files:
            print(f"\n📁 \033[1m\033[93mAll Created Files ({len(all_files)} total):\033[0m")
            for file_path in sorted(all_files):
                size = file_path.stat().st_size
                if "composite" in file_path.name:
                    format_icon = "🎨"
                else:
                    format_icon = "📄" if file_path.suffix == ".svg" else "🖼️"
                print(f"  {format_icon} \033[94m{get_relative_path(file_path)}\033[0m "
                      f"(\033[96m{size:,} bytes\033[0m)")

    print("\n💡 \033[1m\033[93mUse Cases for TUI Responsive Screenshots:\033[0m")
    print("  • \033[92mDocumentation\033[0m: Show how your TUI adapts to different terminal sizes")
    print("  • \033[92mTesting\033[0m: Verify responsive layouts work in various terminals")
    print("  • \033[92mDesign Review\033[0m: Compare layouts across terminal breakpoints")
    print("  • \033[92mDevelopment\033[0m: Test tmux panes, SSH sessions, and IDE integration")
    print("  • \033[92mQA\033[0m: Automated visual regression testing for TUI apps")

    print("\n🎯 \033[1m\033[93mNext Steps:\033[0m")
    print("  • Open SVG files in your browser to view them")
    print("  • Use PNG files for embedding in documentation")
    print("  • View the composite image to see all layouts at once")
    print("  • Compare layouts to ensure responsive design works")
    print("  • Use composite images in presentations and design reviews")
    print("  • Integrate into your CI/CD pipeline for automated testing")


async def create_responsive_composite():
    """Create a composite image showing multiple screen sizes side by side."""
    print("\n🎨 \033[1m\033[93mCreating TUI Responsive Composite Image\033[0m")
    print("   \033[90mStitching together narrow, compact, standard, and wide terminal views\033[0m")

    # Define the sizes we want to showcase - 4 key TUI breakpoints
    showcase_sizes = ["narrow", "compact", "standard", "wide"]
    composite_results = []

    # Capture screenshots for composite
    for size_name in showcase_sizes:
        config = TERMINAL_SIZES[size_name]
        print(f"\n   📸 Capturing {size_name} for composite...")

        try:
            # Capture PNG format for composite (easier to work with)
            result = await capture_app_screenshot(
                ResponsiveApp(size_name=size_name),
                context=f"composite_{size_name}",
                output_format=ScreenshotFormat.PNG,
                metadata={"terminal_size": config["size"]}
            )

            if result.success and result.png_path:
                composite_results.append((size_name, result.png_path, config))
                print(f"   ✅ {size_name}: \033[94m{get_relative_path(result.png_path)}\033[0m")
            else:
                print(f"   ❌ Failed to capture {size_name}")

        except Exception as e:
            print(f"   💥 Error capturing {size_name}: {e}")

    if len(composite_results) < 2:
        print("   ⚠️  Need at least 2 successful captures for composite")
        return None

    # Create composite image
    try:
        return await stitch_images(composite_results)
    except Exception as e:
        print(f"   💥 Failed to create composite: {e}")
        return None


async def stitch_images(image_data: list[tuple[str, Path, dict]]) -> Path:
    """Stitch multiple PNG images together horizontally with labels."""
    print(f"   🔧 Stitching {len(image_data)} images together...")

    # Load all images
    images = []
    labels = []

    for size_name, png_path, config in image_data:
        try:
            img = Image.open(png_path)
            images.append(img)
            width, height = config["size"]
            labels.append(f"{size_name.title()}\n{width}×{height}")
        except Exception as e:
            print(f"   ⚠️  Failed to load {png_path}: {e}")
            continue

    if not images:
        raise ValueError("No images could be loaded")

    # Calculate composite dimensions
    max_height = max(img.height for img in images)
    total_width = sum(img.width for img in images)

    # Add padding between images and space for labels
    padding = 20
    label_height = 60
    composite_width = total_width + (len(images) - 1) * padding
    composite_height = max_height + label_height + padding

    # Create composite image with white background
    composite = Image.new('RGB', (composite_width, composite_height), 'white')
    draw = ImageDraw.Draw(composite)

    # Try to load a font, fall back to default if not available
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 14)
    except OSError:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        except OSError:
            font = ImageFont.load_default()

    # Paste images and add labels
    x_offset = 0
    for _i, (img, label) in enumerate(zip(images, labels)):
        # Paste image
        y_offset = label_height + padding // 2
        composite.paste(img, (x_offset, y_offset))

        # Add label above image (handle multiline text properly)
        label_lines = label.split('\n')
        line_height = 16  # Approximate line height

        for line_idx, line in enumerate(label_lines):
            text_bbox = draw.textbbox((0, 0), line, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_x = x_offset + (img.width - text_width) // 2
            text_y = 10 + (line_idx * line_height)

            # Draw text with shadow for better visibility
            draw.text((text_x + 1, text_y + 1), line, fill='gray', font=font)
            draw.text((text_x, text_y), line, fill='black', font=font)

        x_offset += img.width + padding

    # Add title
    title = "TUI Responsive Breakpoints"
    title_bbox = draw.textbbox((0, 0), title, font=font)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (composite_width - title_width) // 2

    # Draw title with shadow
    draw.text((title_x + 1, composite_height - 25), title, fill='gray', font=font)
    draw.text((title_x, composite_height - 26), title, fill='black', font=font)

    # Save composite image
    output_path = Path("screenshots") / "apps" / "ResponsiveApp" / "tui_responsive_composite.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    composite.save(output_path, 'PNG', optimize=True)

    print(f"   ✅ Composite created: \033[94m{get_relative_path(output_path)}\033[0m")
    print(f"   📏 Dimensions: {composite_width}×{composite_height} pixels")

    return output_path


async def main():
    """Run the complete responsive screenshot demo."""
    print("🚀 Starting responsive screenshot capture demo...")

    # Capture at different terminal sizes
    responsive_results = await capture_responsive_screenshots()

    # Demonstrate quality settings
    quality_results = await capture_quality_comparison()

    # Compare formats
    format_results = await capture_format_comparison()

    # Create responsive composite image
    composite_path = await create_responsive_composite()

    # Show comprehensive summary
    print_summary(responsive_results, quality_results, format_results, composite_path)

    print("\n" + "\033[94m" + "=" * 60 + "\033[0m")
    print("\033[1m\033[92mResponsive screenshot demo completed! 🎉\033[0m")


if __name__ == "__main__":
    asyncio.run(main())
