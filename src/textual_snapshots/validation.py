"""
External validation suite for textual-snapshots.

Implements algorithmic external validation system using pure mathematical
and file-based analysis methods. NO AI/LLM dependencies - only algorithmic
comparison, file analysis, and reference-based validation.

Phase 2 implementation from Enhanced PRP specification (lines 289-337).
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Optional

from .capture import CaptureResult
from .comparison import (
    calculate_file_similarity,
    calculate_svg_similarity,
    validate_svg_structure,
)
from .quality import calculate_quality_metrics
from .types import ValidationResult
from .utils import (
    analyze_platform_consistency,
    calculate_file_hash,
    count_svg_elements,
    extract_platform_from_filename,
    normalize_file_size_score,
)


class ExternalValidationSuite:
    """
    Systematic external validation using algorithmic methods (NO AI/LLM).

    Implements multi-point validation using pure algorithmic comparison,
    file analysis, and reference-based validation methods.
    """

    def __init__(
        self,
        baseline_directory: Optional[Path] = None,
        quality_thresholds: Optional[dict[str, float]] = None,
        platform_reference_directory: Optional[Path] = None,
    ):
        """
        Initialize external validation suite.

        Args:
            baseline_directory: Directory containing human-verified baseline screenshots
            quality_thresholds: Thresholds for quality metrics (0.0-1.0)
            platform_reference_directory: Directory with platform-specific references
        """
        self.baseline_directory = baseline_directory or Path("baselines")
        self.platform_reference_directory = platform_reference_directory or Path("platform_refs")

        # Default quality thresholds - tunable based on requirements
        self.quality_thresholds = quality_thresholds or {
            "file_size_min": 0.3,  # Minimum file size score
            "content_complexity_min": 0.4,  # Minimum content complexity
            "structure_min": 0.5,  # Minimum structure score
            "completeness_min": 0.6,  # Minimum completeness score
            "overall_min": 0.5,  # Minimum overall quality
        }

        # Ensure directories exist
        self.baseline_directory.mkdir(parents=True, exist_ok=True)
        self.platform_reference_directory.mkdir(parents=True, exist_ok=True)

    async def validate_against_references(self, screenshot: CaptureResult) -> ValidationResult:
        """
        Multi-point validation using pure algorithmic comparison.

        Implements comprehensive validation against:
        1. Human-verified baselines (file comparison)
        2. Cross-platform consistency (mathematical analysis)
        3. Quality assessment (algorithmic metrics)

        Args:
            screenshot: Screenshot result to validate

        Returns:
            ValidationResult: Comprehensive validation result
        """
        if not screenshot.success or not screenshot.screenshot_path:
            return ValidationResult(
                is_valid=False,
                confidence=0.0,
                validation_type="external_reference",
                issues=["Screenshot capture failed - cannot validate"],
                metrics={},
            )

        validations = []
        all_issues = []
        all_metrics = {}

        try:
            # 1. Human-verified baselines validation
            baseline_validation = await self._compare_with_human_baselines(screenshot)
            validations.append(("human_baseline", baseline_validation))
            all_issues.extend(baseline_validation.issues)
            all_metrics.update(baseline_validation.metrics)

            # 2. Cross-platform consistency validation
            platform_validation = await self._validate_platform_consistency(screenshot)
            validations.append(("platform_consistency", platform_validation))
            all_issues.extend(platform_validation.issues)
            all_metrics.update(platform_validation.metrics)

            # 3. Quality assessment validation
            quality_validation = self._assess_screenshot_quality_algorithmic(screenshot)
            validations.append(("quality_assessment", quality_validation))
            all_issues.extend(quality_validation.issues)
            all_metrics.update(quality_validation.metrics)

            # Calculate overall validation result
            overall_confidence = sum(v.confidence for _, v in validations) / len(validations)
            overall_valid = all(v.is_valid for _, v in validations)

            return ValidationResult(
                is_valid=overall_valid,
                confidence=overall_confidence,
                validation_type="multi_point_external",
                issues=all_issues,
                metrics={
                    "validation_breakdown": {name: v.confidence for name, v in validations},
                    "individual_results": {name: v.is_valid for name, v in validations},
                    **all_metrics,
                },
            )

        except Exception as e:
            return ValidationResult(
                is_valid=False,
                confidence=0.0,
                validation_type="external_reference",
                issues=[f"Validation system error: {str(e)}"],
                metrics={"error_type": type(e).__name__},
            )

    async def _compare_with_human_baselines(self, screenshot: CaptureResult) -> ValidationResult:
        """
        Compare screenshot with human-verified baselines using file analysis.

        Uses algorithmic file comparison methods:
        - File size similarity analysis
        - Content hash comparison
        - Structural pattern matching (for SVG)
        - Statistical file analysis
        """
        # Check screenshot path early to avoid unnecessary work
        screenshot_path = screenshot.screenshot_path
        if screenshot_path is None:
            return ValidationResult(
                is_valid=False,
                confidence=0.0,
                validation_type="human_baseline",
                issues=["Screenshot path is None"],
                metrics={},
            )

        issues = []
        metrics = {}

        # Find relevant baseline files
        context_name = screenshot.context
        baseline_pattern = f"{context_name}_baseline_*"
        baseline_files = list(self.baseline_directory.glob(baseline_pattern))

        if not baseline_files:
            return ValidationResult(
                is_valid=True,  # No baseline = no contradiction
                confidence=0.3,  # Low confidence without baseline
                validation_type="human_baseline",
                issues=["No human baseline found for comparison"],
                metrics={"baseline_files_found": 0},
            )

        # Analyze against each baseline
        similarity_scores = []

        for baseline_file in baseline_files:
            similarity = calculate_file_similarity(screenshot_path, baseline_file)
            similarity_scores.append(similarity)
            metrics[f"similarity_to_{baseline_file.name}"] = similarity

        # Calculate overall baseline similarity
        avg_similarity = sum(similarity_scores) / len(similarity_scores)
        max_similarity = max(similarity_scores)

        # Determine validation result based on similarity
        similarity_threshold = 0.7  # Tunable threshold
        is_valid = max_similarity >= similarity_threshold

        if not is_valid:
            issues.append(
                f"Low similarity to baselines: max={max_similarity:.2f}, "
                f"avg={avg_similarity:.2f}, threshold={similarity_threshold}"
            )

        metrics.update(
            {
                "baseline_files_found": len(baseline_files),
                "average_similarity": avg_similarity,
                "max_similarity": max_similarity,
                "similarity_threshold": similarity_threshold,
            }
        )

        return ValidationResult(
            is_valid=is_valid,
            confidence=max_similarity,
            validation_type="human_baseline",
            issues=issues,
            metrics=metrics,
        )

    async def _validate_platform_consistency(self, screenshot: CaptureResult) -> ValidationResult:
        """
        Validate cross-platform consistency using mathematical analysis.

        Analyzes platform-specific rendering patterns and consistency
        using algorithmic methods without AI dependencies.
        """
        # Check screenshot path early to avoid unnecessary work
        screenshot_path = screenshot.screenshot_path
        if screenshot_path is None:
            return ValidationResult(
                is_valid=False,
                confidence=0.0,
                validation_type="platform_consistency",
                issues=["Screenshot path is None"],
                metrics={},
            )

        issues = []
        metrics: dict[str, Any] = {}

        # Look for platform-specific reference files
        context_name = screenshot.context
        platform_pattern = f"{context_name}_platform_*"
        platform_refs = list(self.platform_reference_directory.glob(platform_pattern))

        if len(platform_refs) < 2:
            return ValidationResult(
                is_valid=True,  # Cannot validate consistency without multiple platforms
                confidence=0.4,  # Low confidence
                validation_type="platform_consistency",
                issues=["Insufficient platform references for consistency check"],
                metrics={"platform_references": len(platform_refs)},
            )

        # Calculate consistency across platforms
        platform_similarities = []
        platform_names = []

        for ref_file in platform_refs:
            platform_name = extract_platform_from_filename(ref_file.name)
            platform_names.append(platform_name)

            similarity = calculate_file_similarity(screenshot_path, ref_file)
            platform_similarities.append(similarity)
            metrics[f"similarity_to_{platform_name}"] = similarity

        # Analyze consistency patterns
        consistency_analysis = analyze_platform_consistency(platform_similarities)

        # Determine if platform consistency is acceptable
        consistency_threshold = 0.6
        is_consistent = (
            consistency_analysis["variance"] < 0.3
            and consistency_analysis["min_similarity"] > consistency_threshold
        )

        if not is_consistent:
            issues.append(
                f"Platform inconsistency detected: variance={consistency_analysis['variance']:.2f}, "
                f"min_similarity={consistency_analysis['min_similarity']:.2f}"
            )

        metrics.update(
            {
                "platform_count": len(platform_refs),
                "consistency_variance": consistency_analysis["variance"],
                "consistency_score": consistency_analysis["consistency_score"],
                "platform_names": platform_names,
            }
        )

        return ValidationResult(
            is_valid=is_consistent,
            confidence=consistency_analysis["consistency_score"],
            validation_type="platform_consistency",
            issues=issues,
            metrics=metrics,
        )

    def _assess_screenshot_quality_algorithmic(self, screenshot: CaptureResult) -> ValidationResult:
        """
        Assess screenshot quality using pure algorithmic methods.

        Uses mathematical analysis of file properties, content structure,
        and completeness indicators without AI dependencies.
        """
        if not screenshot.screenshot_path or not screenshot.screenshot_path.exists():
            return ValidationResult(
                is_valid=False,
                confidence=0.0,
                validation_type="quality_assessment",
                issues=["Screenshot file does not exist"],
                metrics={},
            )

        # Calculate quality metrics algorithmically
        quality_metrics = calculate_quality_metrics(screenshot)

        # Evaluate against thresholds
        issues = []
        threshold_checks = {
            "file_size": (
                quality_metrics.file_size_score,
                self.quality_thresholds["file_size_min"],
            ),
            "content_complexity": (
                quality_metrics.content_complexity_score,
                self.quality_thresholds["content_complexity_min"],
            ),
            "structure": (
                quality_metrics.structure_score,
                self.quality_thresholds["structure_min"],
            ),
            "completeness": (
                quality_metrics.completeness_score,
                self.quality_thresholds["completeness_min"],
            ),
            "overall": (quality_metrics.overall_score, self.quality_thresholds["overall_min"]),
        }

        for metric_name, (score, threshold) in threshold_checks.items():
            if score < threshold:
                issues.append(f"{metric_name} score {score:.2f} below threshold {threshold:.2f}")

        is_valid = len(issues) == 0
        confidence = quality_metrics.overall_score

        metrics: dict[str, Any] = quality_metrics.to_dict()
        metrics.update(
            {"thresholds_used": self.quality_thresholds, "threshold_failures": len(issues)}
        )

        return ValidationResult(
            is_valid=is_valid,
            confidence=confidence,
            validation_type="quality_assessment",
            issues=issues,
            metrics=metrics,
        )

    # Backward compatibility wrapper methods for tests
    def _calculate_file_similarity(self, file1: Path, file2: Path) -> float:
        """Wrapper for backward compatibility with existing tests."""
        return calculate_file_similarity(file1, file2)

    def _calculate_svg_similarity(self, svg1: Path, svg2: Path) -> float:
        """Wrapper for backward compatibility with existing tests."""
        return calculate_svg_similarity(svg1, svg2)

    def _count_svg_elements(self, root: ET.Element) -> dict[str, int]:
        """Wrapper for backward compatibility with existing tests."""
        return count_svg_elements(root)

    def _extract_platform_from_filename(self, filename: str) -> str:
        """Wrapper for backward compatibility with existing tests."""
        return extract_platform_from_filename(filename)

    def _analyze_platform_consistency(self, similarities: list[float]) -> dict[str, float]:
        """Wrapper for backward compatibility with existing tests."""
        return analyze_platform_consistency(similarities)

    def _normalize_file_size_score(self, file_size: int) -> float:
        """Wrapper for backward compatibility with existing tests."""
        return normalize_file_size_score(file_size)

    def _validate_svg_structure(self, svg_path: Path) -> float:
        """Wrapper for backward compatibility with existing tests."""
        return validate_svg_structure(svg_path)

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Wrapper for backward compatibility with existing tests."""
        return calculate_file_hash(file_path)
