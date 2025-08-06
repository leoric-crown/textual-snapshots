"""
Proactive error detection for textual-snapshots.

Implements algorithmic error detection system using pure mathematical
and file-based analysis methods. NO AI/LLM dependencies - only algorithmic
pattern matching, SVG parsing, and heuristic analysis.

Phase 2 implementation from Enhanced PRP specification (lines 234-287).
"""

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .capture import CaptureResult, ScreenshotFormat


@dataclass
class Issue:
    """Represents a detected issue in screenshot capture."""

    category: str  # Type of issue (empty_screen, layout_issues, rendering_failures)
    description: str  # Human-readable description
    severity: str  # critical, warning, info
    confidence: float = 0.0  # 0.0 to 1.0 confidence in detection
    suggestions: list[str] = field(default_factory=list)  # Possible solutions
    metadata: dict[str, Any] = field(default_factory=dict)  # Additional context


@dataclass
class DetectionResult:
    """Result of proactive error detection."""

    issues_detected: list[Issue]
    detection_confidence: float  # Overall confidence in detection accuracy
    analysis_metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def has_critical_issues(self) -> bool:
        """Check if any critical issues were detected."""
        return any(issue.severity == "critical" for issue in self.issues_detected)

    @property
    def has_warnings(self) -> bool:
        """Check if any warnings were detected."""
        return any(issue.severity == "warning" for issue in self.issues_detected)

    def get_issues_by_severity(self, severity: str) -> list[Issue]:
        """Get issues filtered by severity level."""
        return [issue for issue in self.issues_detected if issue.severity == severity]


class ProactiveErrorDetector:
    """
    Detect common issues using pure algorithmic methods (NO AI/LLM).

    Implements proactive error detection using file analysis, SVG parsing,
    pattern matching, and mathematical thresholds. Designed to catch issues
    before they cause test failures.
    """

    # Error pattern definitions for algorithmic detection
    ERROR_PATTERNS = {
        "empty_screen": [
            "No visible content",
            "Blank screen detected",
            "Screenshot appears empty",
            "Insufficient content detected",
        ],
        "layout_issues": [
            "Overlapping elements detected",
            "Truncated text found",
            "Elements outside viewbox",
            "Layout rendering anomaly",
        ],
        "rendering_failures": [
            "Missing font fallbacks",
            "Broken styling detected",
            "Incomplete element rendering",
            "SVG structure corruption",
        ],
        "capture_quality": [
            "Low quality capture",
            "Capture timing issue",
            "Platform inconsistency",
            "Terminal rendering issue",
        ],
    }

    def __init__(
        self,
        file_size_thresholds: Optional[dict[str, int]] = None,
        content_thresholds: Optional[dict[str, float]] = None,
        enable_svg_analysis: bool = True,
    ):
        """
        Initialize proactive error detector.

        Args:
            file_size_thresholds: File size boundaries for issue detection
            content_thresholds: Content analysis thresholds
            enable_svg_analysis: Whether to perform detailed SVG parsing
        """
        # Default file size thresholds (in bytes)
        self.file_size_thresholds = file_size_thresholds or {
            "critical_min": 1000,  # Below this = critical empty screen
            "warning_min": 2000,  # Below this = warning possible issue
            "optimal_min": 5000,  # Below this = info suboptimal size
            "optimal_max": 1000000,  # Above this = warning large file
            "critical_max": 5000000,  # Above this = critical excessive size
        }

        # Content analysis thresholds
        self.content_thresholds = content_thresholds or {
            "min_text_chars": 5,  # Minimum meaningful text content
            "min_elements": 3,  # Minimum SVG elements for completeness
            "min_element_types": 2,  # Minimum element type diversity
            "text_density_min": 0.1,  # Minimum text density ratio
            "complexity_min": 0.2,  # Minimum content complexity
        }

        self.enable_svg_analysis = enable_svg_analysis

    def detect_common_issues(self, screenshot_result: CaptureResult) -> DetectionResult:
        """
        100% ALGORITHMIC - Pure SVG parsing, file analysis, pattern matching.

        Detects common screenshot issues using mathematical analysis:
        1. File size analysis (mathematical thresholds)
        2. SVG content parsing (XML analysis)
        3. Text extraction and element counting
        4. Rule-based quality scoring

        Args:
            screenshot_result: Screenshot to analyze for issues

        Returns:
            DetectionResult: Comprehensive issue detection result
        """
        if not screenshot_result.success or not screenshot_result.screenshot_path:
            return DetectionResult(
                issues_detected=[
                    Issue(
                        category="capture_failure",
                        description="Screenshot capture failed - cannot analyze",
                        severity="critical",
                        confidence=1.0,
                        suggestions=["Retry capture", "Check app state", "Verify terminal access"],
                    )
                ],
                detection_confidence=1.0,
                analysis_metadata={"analysis_type": "failed_capture"},
            )

        issues = []
        analysis_metadata: dict[str, Any] = {"analysis_methods": []}

        try:
            # 1. File size analysis (mathematical)
            size_issues = self._analyze_file_size(screenshot_result)
            issues.extend(size_issues)
            analysis_metadata["analysis_methods"].append("file_size_analysis")

            # 2. SVG content parsing (XML analysis)
            if self.enable_svg_analysis and screenshot_result.format == ScreenshotFormat.SVG:
                svg_issues = self._analyze_svg_structure(screenshot_result.screenshot_path)
                issues.extend(svg_issues)
                analysis_metadata["analysis_methods"].append("svg_structure_analysis")

                # 3. Content complexity analysis
                content_issues = self._analyze_content_patterns(screenshot_result.screenshot_path)
                issues.extend(content_issues)
                analysis_metadata["analysis_methods"].append("content_pattern_analysis")

            # 4. Platform-specific issue detection
            platform_issues = self._detect_platform_issues(screenshot_result)
            issues.extend(platform_issues)
            analysis_metadata["analysis_methods"].append("platform_issue_detection")

            # Calculate overall detection confidence
            detection_confidence = self._calculate_detection_confidence(issues)

            # Add analysis statistics
            analysis_metadata.update(
                {
                    "total_issues_detected": len(issues),
                    "critical_issues": len([i for i in issues if i.severity == "critical"]),
                    "warning_issues": len([i for i in issues if i.severity == "warning"]),
                    "info_issues": len([i for i in issues if i.severity == "info"]),
                    "file_size_bytes": screenshot_result.file_size_bytes,
                    "format": screenshot_result.format.value
                    if screenshot_result.format
                    else "unknown",
                }
            )

            return DetectionResult(
                issues_detected=issues,
                detection_confidence=detection_confidence,
                analysis_metadata=analysis_metadata,
            )

        except Exception as e:
            # Algorithmic analysis error - return error issue
            return DetectionResult(
                issues_detected=[
                    Issue(
                        category="analysis_error",
                        description=f"Error during algorithmic analysis: {str(e)}",
                        severity="warning",
                        confidence=0.8,
                        suggestions=["Retry analysis", "Check file integrity"],
                        metadata={"error_type": type(e).__name__},
                    )
                ],
                detection_confidence=0.5,
                analysis_metadata={"analysis_error": str(e)},
            )

    def _analyze_file_size(self, screenshot_result: CaptureResult) -> list[Issue]:
        """File size analysis using mathematical thresholds."""
        issues = []
        file_size = screenshot_result.file_size_bytes

        if file_size < self.file_size_thresholds["critical_min"]:
            issues.append(
                Issue(
                    category="empty_screen",
                    description=f"Screenshot file too small ({file_size} bytes) - likely empty screen",
                    severity="critical",
                    confidence=0.9,
                    suggestions=[
                        "Check if app UI is properly rendered",
                        "Increase capture delay",
                        "Verify terminal content before capture",
                    ],
                    metadata={
                        "file_size": file_size,
                        "threshold": self.file_size_thresholds["critical_min"],
                    },
                )
            )
        elif file_size < self.file_size_thresholds["warning_min"]:
            issues.append(
                Issue(
                    category="empty_screen",
                    description=f"Screenshot file small ({file_size} bytes) - possible content issue",
                    severity="warning",
                    confidence=0.7,
                    suggestions=[
                        "Verify app content is fully loaded",
                        "Check for UI rendering delays",
                    ],
                    metadata={
                        "file_size": file_size,
                        "threshold": self.file_size_thresholds["warning_min"],
                    },
                )
            )
        elif file_size > self.file_size_thresholds["critical_max"]:
            issues.append(
                Issue(
                    category="capture_quality",
                    description=f"Screenshot file very large ({file_size} bytes) - possible capture issue",
                    severity="critical",
                    confidence=0.8,
                    suggestions=[
                        "Check for infinite content or loops",
                        "Verify terminal size settings",
                        "Consider format optimization",
                    ],
                    metadata={
                        "file_size": file_size,
                        "threshold": self.file_size_thresholds["critical_max"],
                    },
                )
            )
        elif file_size > self.file_size_thresholds["optimal_max"]:
            issues.append(
                Issue(
                    category="capture_quality",
                    description=f"Screenshot file large ({file_size} bytes) - consider optimization",
                    severity="info",
                    confidence=0.6,
                    suggestions=[
                        "Consider PNG format for complex visuals",
                        "Check for unnecessary content",
                    ],
                    metadata={
                        "file_size": file_size,
                        "threshold": self.file_size_thresholds["optimal_max"],
                    },
                )
            )

        return issues

    def _analyze_svg_structure(self, svg_path: Path) -> list[Issue]:
        """Pure XML parsing - no AI involved."""
        issues = []

        try:
            with open(svg_path, encoding="utf-8") as f:
                svg_content = f.read()

            root = ET.fromstring(svg_content)

            # Count meaningful elements (algorithmic)
            # Use namespace-aware element search
            text_elements = []
            for elem in root.iter():
                if elem.tag.endswith("text") or elem.tag == "text":
                    text_elements.append(elem)
            visible_text = [elem.text for elem in text_elements if elem.text and elem.text.strip()]

            # Element analysis
            all_elements = list(root.iter())
            unique_element_types = set()
            for elem in all_elements:
                tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
                unique_element_types.add(tag)

            # Issue detection based on content analysis
            if len(visible_text) == 0:
                issues.append(
                    Issue(
                        category="empty_screen",
                        description="No visible text found in SVG - possible empty screen",
                        severity="warning",
                        confidence=0.8,
                        suggestions=[
                            "Check if app displays text content",
                            "Verify UI state before capture",
                            "Consider if text-free UI is expected",
                        ],
                        metadata={
                            "text_elements_found": len(text_elements),
                            "visible_text_count": len(visible_text),
                        },
                    )
                )

            if len(all_elements) < self.content_thresholds["min_elements"]:
                issues.append(
                    Issue(
                        category="empty_screen",
                        description=f"Few SVG elements ({len(all_elements)}) - possible incomplete render",
                        severity="warning",
                        confidence=0.7,
                        suggestions=[
                            "Wait for UI rendering to complete",
                            "Check for loading states",
                            "Verify app initialization",
                        ],
                        metadata={
                            "total_elements": len(all_elements),
                            "min_expected": self.content_thresholds["min_elements"],
                        },
                    )
                )

            if len(unique_element_types) < self.content_thresholds["min_element_types"]:
                issues.append(
                    Issue(
                        category="layout_issues",
                        description=f"Low element diversity ({len(unique_element_types)} types) - possible layout issue",
                        severity="info",
                        confidence=0.6,
                        suggestions=[
                            "Verify UI complexity is as expected",
                            "Check for proper component rendering",
                        ],
                        metadata={
                            "unique_types": len(unique_element_types),
                            "element_types": list(unique_element_types),
                        },
                    )
                )

            # Analyze SVG structure validity
            structure_issues = self._validate_svg_structure_integrity(root)
            issues.extend(structure_issues)

        except ET.ParseError as e:
            issues.append(
                Issue(
                    category="rendering_failures",
                    description=f"SVG parsing error - corrupted file structure: {str(e)}",
                    severity="critical",
                    confidence=0.9,
                    suggestions=[
                        "Retry screenshot capture",
                        "Check terminal output for errors",
                        "Verify app rendering completion",
                    ],
                    metadata={"parse_error": str(e)},
                )
            )
        except UnicodeDecodeError:
            issues.append(
                Issue(
                    category="rendering_failures",
                    description="SVG file encoding issue - possible corruption",
                    severity="critical",
                    confidence=0.9,
                    suggestions=[
                        "Retry capture with clean terminal state",
                        "Check for special characters in output",
                    ],
                )
            )

        return issues

    def _validate_svg_structure_integrity(self, root: ET.Element) -> list[Issue]:
        """Validate SVG structure for common rendering issues."""
        issues = []

        # Check for essential SVG attributes
        if "viewBox" not in root.attrib:
            issues.append(
                Issue(
                    category="rendering_failures",
                    description="SVG missing viewBox - may cause rendering inconsistencies",
                    severity="warning",
                    confidence=0.7,
                    suggestions=[
                        "Check SVG generation process",
                        "Verify terminal capture settings",
                    ],
                    metadata={"missing_attribute": "viewBox"},
                )
            )

        # Check for width/height attributes
        has_dimensions = "width" in root.attrib and "height" in root.attrib
        if not has_dimensions:
            issues.append(
                Issue(
                    category="rendering_failures",
                    description="SVG missing width/height attributes - may affect display",
                    severity="info",
                    confidence=0.6,
                    suggestions=[
                        "Verify SVG generation includes dimensions",
                        "Check if viewBox provides sufficient sizing",
                    ],
                    metadata={
                        "has_width": "width" in root.attrib,
                        "has_height": "height" in root.attrib,
                    },
                )
            )

        return issues

    def _analyze_content_patterns(self, svg_path: Path) -> list[Issue]:
        """Analyze content patterns for quality and completeness indicators."""
        issues = []

        try:
            tree = ET.parse(svg_path)
            root = tree.getroot()

            # Text content analysis
            # Use namespace-aware element search
            text_elements = []
            for elem in root.iter():
                if elem.tag.endswith("text") or elem.tag == "text":
                    text_elements.append(elem)
            total_text_length = sum(len(elem.text or "") for elem in text_elements)

            if total_text_length > 0:
                # Calculate text density and patterns
                total_svg_size = svg_path.stat().st_size
                text_density = total_text_length / max(total_svg_size, 1)

                if text_density < self.content_thresholds["text_density_min"]:
                    issues.append(
                        Issue(
                            category="layout_issues",
                            description=f"Low text density ({text_density:.3f}) - possible truncated content",
                            severity="info",
                            confidence=0.5,
                            suggestions=[
                                "Verify all expected text is rendered",
                                "Check for text wrapping issues",
                            ],
                            metadata={
                                "text_density": text_density,
                                "total_text_chars": total_text_length,
                            },
                        )
                    )

            # Pattern detection for common rendering issues
            pattern_issues = self._detect_rendering_patterns(root)
            issues.extend(pattern_issues)

        except Exception as e:
            issues.append(
                Issue(
                    category="analysis_error",
                    description=f"Content pattern analysis failed: {str(e)}",
                    severity="info",
                    confidence=0.3,
                    suggestions=["File may be valid despite analysis error"],
                    metadata={"analysis_error": str(e)},
                )
            )

        return issues

    def _detect_rendering_patterns(self, root: ET.Element) -> list[Issue]:
        """Detect patterns that indicate rendering problems."""
        issues = []

        # Count elements by type for pattern analysis
        element_counts: dict[str, int] = {}
        for elem in root.iter():
            tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
            element_counts[tag] = element_counts.get(tag, 0) + 1

        # Detect unusual patterns
        total_elements = sum(element_counts.values())

        # Too many similar elements might indicate rendering loops
        for elem_type, count in element_counts.items():
            if elem_type != "svg" and count > total_elements * 0.8:  # More than 80% of elements
                issues.append(
                    Issue(
                        category="rendering_failures",
                        description=f"Excessive {elem_type} elements ({count}) - possible rendering loop",
                        severity="warning",
                        confidence=0.7,
                        suggestions=[
                            "Check for infinite loops in app rendering",
                            "Verify app termination conditions",
                        ],
                        metadata={
                            "dominant_element": elem_type,
                            "element_count": count,
                            "total_elements": total_elements,
                        },
                    )
                )

        return issues

    def _detect_platform_issues(self, screenshot_result: CaptureResult) -> list[Issue]:
        """Detect platform-specific rendering or capture issues."""
        issues = []

        # Platform-specific file size patterns (heuristic detection)
        file_size = screenshot_result.file_size_bytes

        # Detect suspiciously uniform file sizes (may indicate platform issues)
        if file_size > 0 and file_size % 1024 == 0:  # Exactly divisible by 1024
            issues.append(
                Issue(
                    category="capture_quality",
                    description=f"File size ({file_size}) exactly divisible by 1024 - possible platform truncation",
                    severity="info",
                    confidence=0.4,
                    suggestions=[
                        "Verify complete capture on current platform",
                        "Compare with captures on other platforms",
                    ],
                    metadata={"file_size": file_size, "modulo_1024": file_size % 1024},
                )
            )

        # Context-based issue detection
        if hasattr(screenshot_result, "context"):
            context_issues = self._analyze_context_patterns(screenshot_result.context)
            issues.extend(context_issues)

        return issues

    def _analyze_context_patterns(self, context: str) -> list[Issue]:
        """Analyze context string for common issue patterns."""
        issues = []

        # Check for error-indicating context names
        error_indicators = ["error", "fail", "crash", "timeout", "exception"]

        context_lower = context.lower()
        for indicator in error_indicators:
            if indicator in context_lower:
                issues.append(
                    Issue(
                        category="capture_quality",
                        description=f"Context name '{context}' suggests error state - verify capture validity",
                        severity="warning",
                        confidence=0.6,
                        suggestions=[
                            "Verify app is in expected state",
                            "Check if error context is intentional for testing",
                        ],
                        metadata={"context": context, "error_indicator": indicator},
                    )
                )
                break  # Only report once per context

        return issues

    def _calculate_detection_confidence(self, issues: list[Issue]) -> float:
        """Calculate overall confidence in issue detection accuracy."""
        if not issues:
            return 1.0  # High confidence in "no issues" when none detected

        # Weighted confidence based on issue severities and individual confidences
        total_weight = 0.0
        weighted_confidence = 0.0

        severity_weights = {"critical": 1.0, "warning": 0.7, "info": 0.4}

        for issue in issues:
            weight = severity_weights.get(issue.severity, 0.5)
            total_weight += weight
            weighted_confidence += issue.confidence * weight

        return weighted_confidence / max(total_weight, 1)

    def get_error_suggestions(self, issues: list[Issue]) -> dict[str, list[str]]:
        """Get actionable suggestions grouped by issue category."""
        suggestions_by_category: dict[str, list[str]] = {}

        for issue in issues:
            category = issue.category
            if category not in suggestions_by_category:
                suggestions_by_category[category] = []

            suggestions_by_category[category].extend(issue.suggestions)

        # Remove duplicates while preserving order
        for category in suggestions_by_category:
            seen = set()
            unique_suggestions = []
            for suggestion in suggestions_by_category[category]:
                if suggestion not in seen:
                    seen.add(suggestion)
                    unique_suggestions.append(suggestion)
            suggestions_by_category[category] = unique_suggestions

        return suggestions_by_category

    def generate_detection_summary(self, detection_result: DetectionResult) -> str:
        """Generate human-readable summary of detection results."""
        issues = detection_result.issues_detected

        if not issues:
            return "No issues detected - screenshot appears healthy"

        critical_count = len([i for i in issues if i.severity == "critical"])
        warning_count = len([i for i in issues if i.severity == "warning"])
        info_count = len([i for i in issues if i.severity == "info"])

        summary_parts = []

        if critical_count > 0:
            summary_parts.append(
                f"{critical_count} critical issue{'s' if critical_count > 1 else ''}"
            )
        if warning_count > 0:
            summary_parts.append(f"{warning_count} warning{'s' if warning_count > 1 else ''}")
        if info_count > 0:
            summary_parts.append(f"{info_count} info item{'s' if info_count > 1 else ''}")

        summary = f"Detected: {', '.join(summary_parts)}"
        summary += f" (confidence: {detection_result.detection_confidence:.2f})"

        return summary
