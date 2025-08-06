"""File comparison and analysis functions for textual-snapshots."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import TYPE_CHECKING

from .utils import calculate_file_hash, count_svg_elements

if TYPE_CHECKING:
    from .capture import ScreenshotFormat


def calculate_file_similarity(file1: Path, file2: Path) -> float:
    """
    Calculate similarity between two files using algorithmic methods.

    Uses multiple similarity measures:
    - File size similarity
    - Content hash similarity (for identical files)
    - Structural similarity (for SVG files)
    """
    if not file1.exists() or not file2.exists():
        return 0.0

    # File size similarity (normalized)
    size1 = file1.stat().st_size
    size2 = file2.stat().st_size
    size_similarity = 1.0 - abs(size1 - size2) / max(size1, size2, 1)

    # Content hash similarity (exact match detection)
    hash1 = calculate_file_hash(file1)
    hash2 = calculate_file_hash(file2)
    hash_similarity = 1.0 if hash1 == hash2 else 0.0

    # If files are identical, return perfect similarity
    if hash_similarity == 1.0:
        return 1.0

    # For SVG files, calculate structural similarity
    structural_similarity = 0.5  # Default middle value
    if file1.suffix.lower() == ".svg" and file2.suffix.lower() == ".svg":
        structural_similarity = calculate_svg_similarity(file1, file2)

    # Weighted combination of similarity measures
    weights = {"size": 0.3, "hash": 0.4, "structure": 0.3}
    overall_similarity = (
        weights["size"] * size_similarity
        + weights["hash"] * hash_similarity
        + weights["structure"] * structural_similarity
    )

    return min(1.0, max(0.0, overall_similarity))


def calculate_svg_similarity(svg1: Path, svg2: Path) -> float:
    """
    Calculate structural similarity between SVG files.

    Analyzes SVG structure, element counts, and patterns
    using XML parsing and mathematical comparison.
    """
    try:
        tree1 = ET.parse(svg1)
        tree2 = ET.parse(svg2)

        # Count elements by type
        elements1 = count_svg_elements(tree1.getroot())
        elements2 = count_svg_elements(tree2.getroot())

        # Calculate element count similarity
        all_elements = set(elements1.keys()) | set(elements2.keys())
        element_similarities = []

        for element in all_elements:
            count1 = elements1.get(element, 0)
            count2 = elements2.get(element, 0)
            max_count = max(count1, count2, 1)
            similarity = 1.0 - abs(count1 - count2) / max_count
            element_similarities.append(similarity)

        return sum(element_similarities) / len(element_similarities)

    except (ET.ParseError, Exception):
        # If SVG parsing fails, fall back to file size comparison
        size1 = svg1.stat().st_size
        size2 = svg2.stat().st_size
        return 1.0 - abs(size1 - size2) / max(size1, size2, 1)


def analyze_content_complexity(file_path: Path) -> float:
    """Analyze content complexity using file-based heuristics."""
    try:
        if file_path.suffix.lower() == ".svg":
            return analyze_svg_complexity(file_path)
        else:
            # For non-SVG files, use file size and basic patterns
            file_size = file_path.stat().st_size
            return min(1.0, file_size / 50000)  # Normalize against 50KB

    except Exception:
        return 0.5  # Default middle score on error


def analyze_svg_complexity(svg_path: Path) -> float:
    """Analyze SVG content complexity using XML parsing."""
    try:
        tree = ET.parse(svg_path)
        root = tree.getroot()

        # Count total elements
        total_elements = len(list(root.iter()))

        # Count unique element types
        element_types = set()
        for element in root.iter():
            tag = element.tag.split("}")[-1] if "}" in element.tag else element.tag
            element_types.add(tag)

        # Analyze text content (complexity indicator)
        text_elements = root.findall(".//text") or []
        total_text_length = sum(len(elem.text or "") for elem in text_elements)

        # Complexity score based on multiple factors
        element_complexity = min(1.0, total_elements / 100)  # Normalize against 100 elements
        diversity_complexity = min(1.0, len(element_types) / 10)  # Normalize against 10 types
        text_complexity = min(1.0, total_text_length / 500)  # Normalize against 500 chars

        # Weighted combination
        return element_complexity * 0.5 + diversity_complexity * 0.3 + text_complexity * 0.2

    except Exception:
        return 0.5  # Default score on parsing error


def analyze_file_structure(file_path: Path, format: ScreenshotFormat) -> float:
    """Analyze file structure validity and completeness."""
    try:
        # Import here to avoid circular import
        from .capture import ScreenshotFormat

        if format == ScreenshotFormat.SVG:
            return validate_svg_structure(file_path)
        else:
            # For other formats, basic file validity check
            return 1.0 if file_path.exists() and file_path.stat().st_size > 0 else 0.0

    except Exception:
        return 0.0


def validate_svg_structure(svg_path: Path) -> float:
    """Validate SVG file structure and return structure quality score."""
    try:
        tree = ET.parse(svg_path)
        root = tree.getroot()

        structure_checks = {
            "has_svg_root": root.tag.endswith("svg"),
            "has_viewbox": "viewBox" in root.attrib,
            "has_content": len(list(root.iter())) > 1,
            "valid_namespace": "xmlns" in root.attrib or "http://www.w3.org/2000/svg" in root.tag,
        }

        passed_checks = sum(structure_checks.values())
        return passed_checks / len(structure_checks)

    except ET.ParseError:
        return 0.0  # Invalid XML structure
    except Exception:
        return 0.5  # Unknown error, give benefit of doubt


def analyze_content_completeness(file_path: Path) -> float:
    """Analyze if file appears to contain complete, meaningful content."""
    try:
        file_size = file_path.stat().st_size

        if file_path.suffix.lower() == ".svg":
            return analyze_svg_completeness(file_path, file_size)
        else:
            # For non-SVG, use file size heuristics
            if file_size < 1000:
                return 0.3  # Probably incomplete
            elif file_size > 10000:
                return 1.0  # Likely complete
            else:
                return file_size / 10000  # Linear scale

    except Exception:
        return 0.5


def analyze_svg_completeness(svg_path: Path, file_size: int) -> float:
    """Analyze SVG completeness using content analysis."""
    try:
        tree = ET.parse(svg_path)
        root = tree.getroot()

        # Check for common completeness indicators
        completeness_indicators = {
            "has_text": len(root.findall(".//text")) > 0,
            "has_shapes": len(
                root.findall(
                    './/*[local-name()="rect" or local-name()="circle" or local-name()="path"]'
                )
            )
            > 0,
            "reasonable_size": file_size > 2000,
            "has_styles": len(root.findall(".//*[@style]")) > 0
            or len(root.findall(".//style")) > 0,
        }

        completeness_score = sum(completeness_indicators.values()) / len(completeness_indicators)

        # Adjust score based on file size (larger usually means more complete)
        size_factor = min(1.0, file_size / 20000)  # Normalize against 20KB

        return completeness_score * 0.7 + size_factor * 0.3

    except Exception:
        return 0.5
