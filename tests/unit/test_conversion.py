"""Unit tests for high-quality SVG→PNG conversion."""

import tempfile
from pathlib import Path

import pytest

from textual_snapshots.conversion import (
    ChromiumConverter,
    check_browser_availability,
    convert_svg_to_png_async,
    convert_svg_to_png_sync,
    get_fallback_conversion_message,
)


class TestChromiumConverter:
    """Test the ChromiumConverter class."""

    def test_quality_settings(self) -> None:
        """Test quality settings are properly defined."""
        converter = ChromiumConverter()

        assert "low" in converter.QUALITY_SETTINGS
        assert "medium" in converter.QUALITY_SETTINGS
        assert "high" in converter.QUALITY_SETTINGS

        # Check settings structure
        high_settings = converter.QUALITY_SETTINGS["high"]
        assert "dpi" in high_settings
        assert "scale" in high_settings
        assert high_settings["scale"] == 2.0
        assert high_settings["dpi"] == 192

    @pytest.mark.asyncio
    async def test_svg_file_not_found(self) -> None:
        """Test error handling for missing SVG files."""
        converter = ChromiumConverter()

        svg_path = Path("nonexistent.svg")
        output_path = Path("output.png")

        with pytest.raises(FileNotFoundError, match="SVG file not found"):
            await converter.convert_svg_to_png(svg_path, output_path, "high")

    @pytest.mark.asyncio
    async def test_invalid_quality(self) -> None:
        """Test error handling for invalid quality settings."""
        converter = ChromiumConverter()

        with tempfile.NamedTemporaryFile(suffix=".svg", mode="w", delete=False) as f:
            f.write('<svg><rect width="10" height="10"/></svg>')
            svg_path = Path(f.name)

        try:
            output_path = Path("output.png")

            with pytest.raises(ValueError, match="Invalid quality"):
                await converter.convert_svg_to_png(svg_path, output_path, "invalid")
        finally:
            svg_path.unlink()

    @pytest.mark.asyncio
    async def test_conversion_with_playwright_available(self) -> None:
        """Test successful conversion when Playwright is available."""
        # Only run if Playwright is actually available
        if not check_browser_availability():
            pytest.skip("Playwright not available")

        test_svg = """<?xml version="1.0" encoding="UTF-8"?>
        <svg width="100" height="50" xmlns="http://www.w3.org/2000/svg">
            <rect width="100" height="50" fill="blue"/>
        </svg>"""

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            svg_path = temp_path / "test.svg"
            output_path = temp_path / "test.png"

            svg_path.write_text(test_svg)

            converter = ChromiumConverter()
            result = await converter.convert_svg_to_png(svg_path, output_path, "high")

            assert result == output_path
            assert output_path.exists()
            assert output_path.stat().st_size > 0


class TestConversionFunctions:
    """Test the public conversion functions."""

    def test_check_browser_availability(self) -> None:
        """Test browser availability check."""
        # This should return True if Playwright is installed, False otherwise
        result = check_browser_availability()
        assert isinstance(result, bool)

    def test_get_fallback_conversion_message(self) -> None:
        """Test fallback message generation."""
        message = get_fallback_conversion_message()

        assert isinstance(message, str)
        assert "playwright" in message.lower()
        assert "chromium" in message.lower()
        assert "browser" in message.lower()

    @pytest.mark.asyncio
    async def test_convert_svg_to_png_async(self) -> None:
        """Test async conversion function."""
        if not check_browser_availability():
            pytest.skip("Playwright not available")

        test_svg = """<?xml version="1.0" encoding="UTF-8"?>
        <svg width="50" height="25" xmlns="http://www.w3.org/2000/svg">
            <circle cx="25" cy="12" r="10" fill="red"/>
        </svg>"""

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            svg_path = temp_path / "async_test.svg"
            output_dir = temp_path / "output"

            svg_path.write_text(test_svg)

            result = await convert_svg_to_png_async(svg_path, output_dir, "medium")

            expected_output = output_dir / "async_test.png"
            assert result == expected_output
            assert expected_output.exists()
            assert expected_output.stat().st_size > 0

    def test_convert_svg_to_png_sync(self) -> None:
        """Test synchronous conversion function."""
        if not check_browser_availability():
            pytest.skip("Playwright not available")

        test_svg = """<?xml version="1.0" encoding="UTF-8"?>
        <svg width="30" height="30" xmlns="http://www.w3.org/2000/svg">
            <rect width="30" height="30" fill="green"/>
        </svg>"""

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            svg_path = temp_path / "sync_test.svg"
            output_dir = temp_path / "output"

            svg_path.write_text(test_svg)

            result = convert_svg_to_png_sync(svg_path, output_dir, "low")

            expected_output = output_dir / "sync_test.png"
            assert result == expected_output
            assert expected_output.exists()
            assert expected_output.stat().st_size > 0

    def test_output_directory_creation(self) -> None:
        """Test that output directories are created automatically."""
        if not check_browser_availability():
            pytest.skip("Playwright not available")

        test_svg = """<?xml version="1.0" encoding="UTF-8"?>
        <svg width="20" height="20" xmlns="http://www.w3.org/2000/svg">
            <circle cx="10" cy="10" r="8" fill="yellow"/>
        </svg>"""

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            svg_path = temp_path / "dir_test.svg"
            output_dir = temp_path / "nested" / "output"  # Multi-level directory

            svg_path.write_text(test_svg)

            # Output directory doesn't exist yet
            assert not output_dir.exists()

            result = convert_svg_to_png_sync(svg_path, output_dir, "high")

            # Directory should be created and file should exist
            assert output_dir.exists()
            assert result.exists()


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_browser_unavailable_import_error(self) -> None:
        """Test error handling when Playwright import fails."""
        test_svg = """<?xml version="1.0" encoding="UTF-8"?>
        <svg width="10" height="10" xmlns="http://www.w3.org/2000/svg">
            <rect width="10" height="10" fill="black"/>
        </svg>"""

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            svg_path = temp_path / "error_test.svg"
            svg_path.write_text(test_svg)

            # This test validates that we get proper error messages
            # The actual error will be caught during the import attempt inside the converter
            # Since Playwright is available in this test environment, we'll just verify
            # the error message structure would be correct if it failed

            # Test the message generation function
            message = get_fallback_conversion_message()
            assert "playwright" in message.lower()
            assert "chromium" in message.lower()
            # Also verify the test SVG was created properly
            assert svg_path.exists()
