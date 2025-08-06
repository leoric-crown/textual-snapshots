"""High-quality SVG to PNG conversion using Chromium browser engine."""

import asyncio
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ChromiumConverter:
    """High-quality SVG→PNG conversion using Chromium browser."""

    QUALITY_SETTINGS = {
        "low": {"dpi": 96, "scale": 1.0},
        "medium": {"dpi": 144, "scale": 1.5},
        "high": {"dpi": 192, "scale": 2.0},
    }

    async def convert_svg_to_png(
        self, svg_path: Path, output_path: Path, quality: str = "high"
    ) -> Path:
        """Convert SVG to PNG using Chromium browser for perfect quality.

        Args:
            svg_path: Path to input SVG file
            output_path: Path for output PNG file
            quality: Quality setting - "low", "medium", or "high"

        Returns:
            Path to created PNG file

        Raises:
            FileNotFoundError: If SVG file doesn't exist
            RuntimeError: If browser automation fails
        """
        if not svg_path.exists():
            raise FileNotFoundError(f"SVG file not found: {svg_path}")

        if quality not in self.QUALITY_SETTINGS:
            raise ValueError(
                f"Invalid quality '{quality}'. Must be one of: {list(self.QUALITY_SETTINGS.keys())}"
            )

        # Read SVG content
        try:
            svg_content = svg_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # Try with different encoding
            svg_content = svg_path.read_text(encoding="latin-1")

        # Get quality settings
        settings = self.QUALITY_SETTINGS[quality]

        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise RuntimeError(
                "Playwright not installed. Install with: pip install playwright && playwright install chromium"
            ) from None

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-gpu",
                        "--disable-web-security",
                    ],
                )
                page = await browser.new_page(device_scale_factor=settings["scale"])

                # Create HTML wrapper for SVG with proper styling
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1">
                    <style>
                        body {{
                            margin: 0;
                            padding: 0;
                            background: transparent;
                        }}
                        svg {{
                            display: block;
                            max-width: 100%;
                            height: auto;
                        }}
                    </style>
                </head>
                <body>{svg_content}</body>
                </html>
                """

                await page.set_content(html_content, wait_until="networkidle")

                # Get SVG dimensions for precise cropping
                svg_element = await page.query_selector("svg")
                if svg_element:
                    bbox = await svg_element.bounding_box()
                    if bbox and bbox["width"] > 0 and bbox["height"] > 0:
                        # Take screenshot with exact SVG dimensions
                        await page.screenshot(
                            path=output_path, clip=bbox, type="png", full_page=False
                        )
                    else:
                        # Fallback: get viewport size
                        await page.screenshot(path=output_path, type="png", full_page=False)
                else:
                    # Final fallback: full page screenshot
                    await page.screenshot(path=output_path, type="png", full_page=True)

                await browser.close()

        except Exception as e:
            logger.error(f"Browser automation failed for {svg_path}: {e}")
            raise RuntimeError(f"Failed to convert SVG to PNG using browser: {e}") from e

        if not output_path.exists():
            raise RuntimeError(f"Conversion completed but output file not found: {output_path}")

        return output_path


async def convert_svg_to_png_async(svg_path: Path, output_dir: Path, quality: str) -> Path:
    """Public async interface for SVG→PNG conversion.

    Args:
        svg_path: Path to input SVG file
        output_dir: Directory for output PNG file
        quality: Quality setting - "low", "medium", or "high"

    Returns:
        Path to created PNG file
    """
    converter = ChromiumConverter()
    output_path = output_dir / f"{svg_path.stem}.png"
    output_dir.mkdir(parents=True, exist_ok=True)

    return await converter.convert_svg_to_png(svg_path, output_path, quality)


def convert_svg_to_png_sync(svg_path: Path, output_dir: Path, quality: str) -> Path:
    """Synchronous wrapper for CLI usage.

    Args:
        svg_path: Path to input SVG file
        output_dir: Directory for output PNG file
        quality: Quality setting - "low", "medium", or "high"

    Returns:
        Path to created PNG file
    """
    return asyncio.run(convert_svg_to_png_async(svg_path, output_dir, quality))


def check_browser_availability() -> bool:
    """Check if Playwright and Chromium are available.

    Returns:
        True if browser conversion is available, False otherwise
    """
    try:
        import importlib.util

        return importlib.util.find_spec("playwright") is not None
    except ImportError:
        return False


def get_fallback_conversion_message() -> str:
    """Get helpful message for setting up browser conversion."""
    return (
        "High-quality browser conversion not available. Install with:\n"
        "  pip install playwright\n"
        "  playwright install chromium\n\n"
        "Falling back to librsvg if available..."
    )
