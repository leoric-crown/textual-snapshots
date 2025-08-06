"""Utility functions for textual-snapshots validation system."""

import hashlib
import xml.etree.ElementTree as ET
from pathlib import Path


def calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA256 hash of file content."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def count_svg_elements(root: ET.Element) -> dict[str, int]:
    """Count elements in SVG by tag name."""
    element_counts: dict[str, int] = {}

    def count_recursive(element: ET.Element) -> None:
        tag = element.tag.split("}")[-1] if "}" in element.tag else element.tag
        element_counts[tag] = element_counts.get(tag, 0) + 1

        for child in element:
            count_recursive(child)

    count_recursive(root)
    return element_counts


def extract_platform_from_filename(filename: str) -> str:
    """Extract platform name from reference filename."""
    # Expected format: context_platform_darwin_timestamp.svg
    parts = filename.split("_")
    for i, part in enumerate(parts):
        if part == "platform" and i + 1 < len(parts) and i + 2 < len(parts):
            # Check that there's a platform name AND a timestamp after "platform"
            platform = parts[i + 1]
            # Ensure the next part looks like a timestamp (numeric)
            timestamp_part = parts[i + 2].split(".")[0]  # Remove extension
            if timestamp_part.isdigit():
                return platform.split(".")[0]  # Remove file extension
    return "unknown"


def analyze_platform_consistency(similarities: list[float]) -> dict[str, float]:
    """Analyze consistency metrics from similarity scores."""
    if not similarities:
        return {"variance": 1.0, "consistency_score": 0.0, "min_similarity": 0.0}

    mean_similarity = sum(similarities) / len(similarities)
    variance = sum((s - mean_similarity) ** 2 for s in similarities) / len(similarities)
    min_similarity = min(similarities)

    # Consistency score: high when variance is low and min similarity is high
    consistency_score = (1.0 - variance) * min_similarity

    return {
        "variance": variance,
        "consistency_score": consistency_score,
        "min_similarity": min_similarity,
        "mean_similarity": mean_similarity,
    }


def normalize_file_size_score(file_size: int) -> float:
    """Normalize file size to 0.0-1.0 score based on expected ranges."""
    # Expected size ranges for screenshot files
    min_expected = 2000  # 2KB minimum for meaningful content
    optimal_min = 10000  # 10KB for good quality
    optimal_max = 500000  # 500KB reasonable maximum
    max_expected = 2000000  # 2MB absolute maximum

    if file_size < min_expected:
        return 0.0
    elif file_size >= optimal_min and file_size <= optimal_max:
        return 1.0
    elif file_size < optimal_min:
        return (file_size - min_expected) / (optimal_min - min_expected)
    else:  # file_size > optimal_max
        # Linear decrease from 1.0 at optimal_max to 0.0 at max_expected
        decrease_ratio = (file_size - optimal_max) / (max_expected - optimal_max)
        return max(0.0, 1.0 - decrease_ratio)
