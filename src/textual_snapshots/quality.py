"""Quality assessment functions for textual-snapshots."""

from .capture import CaptureResult
from .comparison import (
    analyze_content_completeness,
    analyze_content_complexity,
    analyze_file_structure,
)
from .types import QualityMetrics
from .utils import normalize_file_size_score


def calculate_quality_metrics(screenshot: CaptureResult) -> QualityMetrics:
    """
    Calculate comprehensive quality metrics using algorithmic analysis.

    Analyzes file size, content complexity, structure, and completeness
    using mathematical methods without AI dependencies.
    """
    file_path = screenshot.screenshot_path
    if file_path is None:
        # Handle case where screenshot_path is None
        return QualityMetrics(
            file_size_score=0.0,
            content_complexity_score=0.0,
            structure_score=0.0,
            completeness_score=0.0,
            overall_score=0.0,
        )

    # File size score (normalized against expected ranges)
    file_size = screenshot.file_size_bytes
    file_size_score = normalize_file_size_score(file_size)

    # Content complexity score (based on file content analysis)
    content_complexity_score = analyze_content_complexity(file_path)

    # Structure score (based on file format validation)
    structure_score = analyze_file_structure(file_path, screenshot.format)

    # Completeness score (based on expected content patterns)
    completeness_score = analyze_content_completeness(file_path)

    # Overall score (weighted combination)
    weights = {"size": 0.2, "complexity": 0.3, "structure": 0.3, "completeness": 0.2}
    overall_score = (
        weights["size"] * file_size_score
        + weights["complexity"] * content_complexity_score
        + weights["structure"] * structure_score
        + weights["completeness"] * completeness_score
    )

    return QualityMetrics(
        file_size_score=file_size_score,
        content_complexity_score=content_complexity_score,
        structure_score=structure_score,
        completeness_score=completeness_score,
        overall_score=overall_score,
    )
