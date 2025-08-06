"""
Tests for proactive error detection functionality.

Tests the algorithmic error detection system including:
- File size based issue detection
- SVG structure analysis
- Content pattern analysis
- Platform-specific issue detection
- Error categorization and confidence scoring

Phase 2 testing from Enhanced PRP specification.
"""

import tempfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from textual_snapshots.capture import CaptureResult, ScreenshotFormat
from textual_snapshots.detection import (
    DetectionResult,
    Issue,
    ProactiveErrorDetector,
)


class TestProactiveErrorDetector:
    """Test proactive error detection functionality."""

    @pytest.fixture
    def detector(self):
        """Create default error detector."""
        return ProactiveErrorDetector()

    @pytest.fixture
    def detector_with_custom_thresholds(self):
        """Create error detector with custom thresholds."""
        custom_file_thresholds = {
            "critical_min": 500,
            "warning_min": 1000,
            "optimal_min": 2000,
            "optimal_max": 500000,
            "critical_max": 2000000,
        }

        custom_content_thresholds = {
            "min_text_chars": 10,
            "min_elements": 5,
            "min_element_types": 3,
            "text_density_min": 0.2,
            "complexity_min": 0.3,
        }

        return ProactiveErrorDetector(
            file_size_thresholds=custom_file_thresholds,
            content_thresholds=custom_content_thresholds,
        )

    @pytest.fixture
    def temp_screenshot_dir(self):
        """Create temporary directory for test screenshots."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def sample_svg_content(self):
        """Sample SVG content for testing."""
        return """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 80" width="120" height="80">
    <rect x="10" y="10" width="30" height="30" style="fill:blue"/>
    <circle cx="70" cy="30" r="15" style="fill:red"/>
    <text x="20" y="70">Test Application Content</text>
    <path d="M20,75 L80,75" style="stroke:black;stroke-width:2"/>
    <g>
        <rect x="90" y="50" width="20" height="15" style="fill:green"/>
    </g>
</svg>"""

    @pytest.fixture
    def empty_svg_content(self):
        """Empty SVG content for testing."""
        return """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"/>"""

    @pytest.fixture
    def malformed_svg_content(self):
        """Malformed SVG for testing error handling."""
        return """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <rect x="10" y="10" width="30" height="30"
    <!-- Missing closing tag and quotes -->
</svg>"""

    def create_mock_capture_result(
        self,
        success: bool = True,
        screenshot_path: Path = None,
        file_size: int = 10000,
        format: ScreenshotFormat = ScreenshotFormat.SVG,
        context: str = "test_context",
        svg_content: str = None,
        temp_dir: Path = None,
    ) -> CaptureResult:
        """Create mock capture result for testing."""
        if screenshot_path is None and temp_dir and svg_content:
            screenshot_path = temp_dir / "test.svg"
            screenshot_path.write_text(svg_content)
            file_size = screenshot_path.stat().st_size

        app_context = MagicMock()
        app_context.context_name = context
        app_context.app_id = f"{context}_123"

        return CaptureResult(
            success=success,
            screenshot_path=screenshot_path,
            svg_path=screenshot_path,
            format=format,
            file_size_bytes=file_size,
            svg_size_bytes=file_size,
            context=context,
            app_context=app_context,
            timestamp=datetime.now(timezone.utc),
        )

    def test_detector_initialization_defaults(self):
        """Test detector initialization with default parameters."""
        detector = ProactiveErrorDetector()

        assert detector.file_size_thresholds["critical_min"] == 1000
        assert detector.file_size_thresholds["warning_min"] == 2000
        assert detector.content_thresholds["min_text_chars"] == 5
        assert detector.enable_svg_analysis is True

    def test_detector_initialization_custom(self):
        """Test detector initialization with custom parameters."""
        custom_file_thresholds = {"critical_min": 500, "warning_min": 1500}
        custom_content_thresholds = {"min_text_chars": 10}

        detector = ProactiveErrorDetector(
            file_size_thresholds=custom_file_thresholds,
            content_thresholds=custom_content_thresholds,
            enable_svg_analysis=False,
        )

        assert detector.file_size_thresholds["critical_min"] == 500
        assert detector.file_size_thresholds["warning_min"] == 1500
        assert detector.content_thresholds["min_text_chars"] == 10
        assert detector.enable_svg_analysis is False

    def test_detect_common_issues_failed_capture(self, detector):
        """Test detection with failed capture result."""
        failed_result = CaptureResult(
            success=False,
            screenshot_path=None,
            context="failed_test",
            app_context=MagicMock(),
            error_message="Capture failed",
        )

        result = detector.detect_common_issues(failed_result)

        assert isinstance(result, DetectionResult)
        assert len(result.issues_detected) == 1
        assert result.issues_detected[0].category == "capture_failure"
        assert result.issues_detected[0].severity == "critical"
        assert result.detection_confidence == 1.0

    def test_file_size_analysis_critical_small(self, detector, temp_screenshot_dir):
        """Test detection of critically small files."""
        small_content = "<svg></svg>"  # Very small file
        screenshot_path = temp_screenshot_dir / "small.svg"
        screenshot_path.write_text(small_content)

        capture_result = self.create_mock_capture_result(
            screenshot_path=screenshot_path,
            file_size=len(small_content),
            temp_dir=temp_screenshot_dir,
        )

        result = detector.detect_common_issues(capture_result)

        # Should detect critical empty screen issue
        critical_issues = result.get_issues_by_severity("critical")
        assert len(critical_issues) >= 1
        assert any("too small" in issue.description for issue in critical_issues)

    def test_file_size_analysis_warning_small(self, detector, temp_screenshot_dir):
        """Test detection of warning-level small files."""
        # Create file between critical and warning thresholds
        content = "<svg>" + "x" * 1500 + "</svg>"  # Between 1000 and 2000 bytes
        screenshot_path = temp_screenshot_dir / "warning.svg"
        screenshot_path.write_text(content)

        capture_result = self.create_mock_capture_result(
            screenshot_path=screenshot_path, file_size=len(content), temp_dir=temp_screenshot_dir
        )

        result = detector.detect_common_issues(capture_result)

        # Should detect warning level issue
        warning_issues = result.get_issues_by_severity("warning")
        assert any("small" in issue.description.lower() for issue in warning_issues)

    def test_file_size_analysis_large_file(self, detector, temp_screenshot_dir):
        """Test detection of excessively large files."""
        large_content = "<svg>" + "x" * 6000000 + "</svg>"  # Over 6MB
        screenshot_path = temp_screenshot_dir / "large.svg"
        screenshot_path.write_text(large_content)

        capture_result = self.create_mock_capture_result(
            screenshot_path=screenshot_path,
            file_size=len(large_content),
            temp_dir=temp_screenshot_dir,
        )

        result = detector.detect_common_issues(capture_result)

        # Should detect critical large file issue
        critical_issues = result.get_issues_by_severity("critical")
        assert any("very large" in issue.description for issue in critical_issues)

    def test_svg_structure_analysis_valid_svg(
        self, detector, temp_screenshot_dir, sample_svg_content
    ):
        """Test SVG analysis with valid SVG content."""
        capture_result = self.create_mock_capture_result(
            svg_content=sample_svg_content, temp_dir=temp_screenshot_dir
        )

        result = detector.detect_common_issues(capture_result)

        # Should not detect major structural issues with good SVG
        critical_issues = result.get_issues_by_severity("critical")
        structure_issues = [i for i in critical_issues if "svg" in i.description.lower()]
        assert len(structure_issues) == 0

    def test_svg_structure_analysis_empty_svg(
        self, detector, temp_screenshot_dir, empty_svg_content
    ):
        """Test SVG analysis with empty SVG content."""
        capture_result = self.create_mock_capture_result(
            svg_content=empty_svg_content, temp_dir=temp_screenshot_dir
        )

        result = detector.detect_common_issues(capture_result)

        # Should detect issues with empty SVG
        warning_issues = result.get_issues_by_severity("warning")
        assert any("text" in issue.description.lower() for issue in warning_issues)
        assert any("elements" in issue.description.lower() for issue in warning_issues)

    def test_svg_structure_analysis_malformed_svg(
        self, detector, temp_screenshot_dir, malformed_svg_content
    ):
        """Test SVG analysis with malformed SVG."""
        capture_result = self.create_mock_capture_result(
            svg_content=malformed_svg_content, temp_dir=temp_screenshot_dir
        )

        result = detector.detect_common_issues(capture_result)

        # Should detect critical parsing error
        critical_issues = result.get_issues_by_severity("critical")
        assert any("parsing error" in issue.description.lower() for issue in critical_issues)

    def test_svg_structure_analysis_disabled(self, temp_screenshot_dir, sample_svg_content):
        """Test that SVG analysis can be disabled."""
        detector = ProactiveErrorDetector(enable_svg_analysis=False)

        capture_result = self.create_mock_capture_result(
            svg_content=sample_svg_content, temp_dir=temp_screenshot_dir
        )

        result = detector.detect_common_issues(capture_result)

        # Should not perform SVG-specific analysis
        [i for i in result.issues_detected if "svg" in i.description.lower()]
        # Only file size analysis should remain
        assert result.analysis_metadata["analysis_methods"] == [
            "file_size_analysis",
            "platform_issue_detection",
        ]

    def test_content_pattern_analysis(self, detector, temp_screenshot_dir):
        """Test content pattern analysis functionality."""
        # SVG with repetitive elements (potential rendering loop)
        repetitive_svg = (
            """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
"""
            + '    <rect x="10" y="10" width="5" height="5"/>\n' * 50
            + "</svg>"
        )

        capture_result = self.create_mock_capture_result(
            svg_content=repetitive_svg, temp_dir=temp_screenshot_dir
        )

        result = detector.detect_common_issues(capture_result)

        # Should detect potential rendering loop
        warning_issues = result.get_issues_by_severity("warning")
        loop_issues = [
            i
            for i in warning_issues
            if "excessive" in i.description.lower() or "loop" in i.description.lower()
        ]
        assert len(loop_issues) > 0

    def test_platform_issue_detection(self, detector, temp_screenshot_dir):
        """Test platform-specific issue detection."""
        # Create file with size exactly divisible by 1024 (potential platform truncation)
        content = "x" * 2048  # Exactly 2048 bytes
        screenshot_path = temp_screenshot_dir / "platform.svg"
        screenshot_path.write_text(content)

        capture_result = self.create_mock_capture_result(
            screenshot_path=screenshot_path, file_size=2048, temp_dir=temp_screenshot_dir
        )

        result = detector.detect_common_issues(capture_result)

        # Should detect potential platform truncation
        info_issues = result.get_issues_by_severity("info")
        platform_issues = [i for i in info_issues if "1024" in i.description]
        assert len(platform_issues) > 0

    def test_context_pattern_analysis_error_context(
        self, detector, temp_screenshot_dir, sample_svg_content
    ):
        """Test context analysis for error-indicating names."""
        capture_result = self.create_mock_capture_result(
            svg_content=sample_svg_content,
            temp_dir=temp_screenshot_dir,
            context="error_state_screenshot",  # Contains "error"
        )

        result = detector.detect_common_issues(capture_result)

        # Should detect context-based warning
        warning_issues = result.get_issues_by_severity("warning")
        context_issues = [i for i in warning_issues if "context" in i.description.lower()]
        assert len(context_issues) > 0

    def test_detection_confidence_calculation(self, detector, temp_screenshot_dir):
        """Test overall detection confidence calculation."""
        # Create scenario with mixed issue severities
        small_content = "<svg></svg>"  # Will trigger critical issue
        screenshot_path = temp_screenshot_dir / "mixed.svg"
        screenshot_path.write_text(small_content)

        capture_result = self.create_mock_capture_result(
            screenshot_path=screenshot_path,
            file_size=len(small_content),
            context="warning_test_context",  # Will trigger warning
            temp_dir=temp_screenshot_dir,
        )

        result = detector.detect_common_issues(capture_result)

        # Should have reasonable confidence calculation
        assert 0.0 <= result.detection_confidence <= 1.0
        assert result.detection_confidence > 0.5  # Should be reasonably confident

    def test_detection_confidence_no_issues(
        self, detector, temp_screenshot_dir, sample_svg_content
    ):
        """Test detection confidence when no issues found."""
        capture_result = self.create_mock_capture_result(
            svg_content=sample_svg_content, temp_dir=temp_screenshot_dir
        )

        result = detector.detect_common_issues(capture_result)

        # High confidence when no issues detected
        if len(result.issues_detected) == 0:
            assert result.detection_confidence == 1.0

    def test_error_suggestions_grouping(self, detector):
        """Test grouping of error suggestions by category."""
        # Create issues with different categories
        issues = [
            Issue(
                "empty_screen",
                "Test issue 1",
                "critical",
                suggestions=["Suggestion 1", "Suggestion 2"],
            ),
            Issue(
                "empty_screen",
                "Test issue 2",
                "warning",
                suggestions=["Suggestion 2", "Suggestion 3"],
            ),
            Issue("layout_issues", "Test issue 3", "info", suggestions=["Suggestion 4"]),
        ]

        suggestions = detector.get_error_suggestions(issues)

        assert "empty_screen" in suggestions
        assert "layout_issues" in suggestions

        # Should remove duplicates
        empty_suggestions = suggestions["empty_screen"]
        assert len(empty_suggestions) == 3  # Should have unique suggestions only
        assert "Suggestion 1" in empty_suggestions
        assert "Suggestion 2" in empty_suggestions
        assert "Suggestion 3" in empty_suggestions

    def test_detection_summary_generation(self, detector):
        """Test generation of human-readable detection summary."""
        # Test with no issues
        no_issues_result = DetectionResult(issues_detected=[], detection_confidence=1.0)
        summary = detector.generate_detection_summary(no_issues_result)
        assert "No issues detected" in summary

        # Test with mixed issues
        issues = [
            Issue("test", "Critical issue", "critical"),
            Issue("test", "Warning issue", "warning"),
            Issue("test", "Info issue", "info"),
        ]
        mixed_result = DetectionResult(issues_detected=issues, detection_confidence=0.75)
        summary = detector.generate_detection_summary(mixed_result)

        assert "1 critical issue" in summary
        assert "1 warning" in summary
        assert "1 info item" in summary
        assert "0.75" in summary

    def test_analysis_metadata_collection(self, detector, temp_screenshot_dir, sample_svg_content):
        """Test that analysis metadata is properly collected."""
        capture_result = self.create_mock_capture_result(
            svg_content=sample_svg_content, temp_dir=temp_screenshot_dir
        )

        result = detector.detect_common_issues(capture_result)

        # Should have comprehensive metadata
        metadata = result.analysis_metadata
        assert "analysis_methods" in metadata
        assert "total_issues_detected" in metadata
        assert "critical_issues" in metadata
        assert "warning_issues" in metadata
        assert "info_issues" in metadata
        assert "file_size_bytes" in metadata
        assert "format" in metadata

        # Should track which analysis methods were used
        methods = metadata["analysis_methods"]
        assert "file_size_analysis" in methods
        if detector.enable_svg_analysis:
            assert "svg_structure_analysis" in methods
            assert "content_pattern_analysis" in methods

    def test_custom_thresholds_respected(
        self, detector_with_custom_thresholds, temp_screenshot_dir
    ):
        """Test that custom thresholds are properly respected."""
        # Create file that would be OK with default thresholds but triggers custom ones
        content = (
            "<svg></svg>" + "x" * 400
        )  # Around 409 bytes - below custom critical_min (500) but above some content
        screenshot_path = temp_screenshot_dir / "custom_threshold.svg"
        screenshot_path.write_text(content)

        capture_result = self.create_mock_capture_result(
            screenshot_path=screenshot_path, file_size=len(content), temp_dir=temp_screenshot_dir
        )

        result = detector_with_custom_thresholds.detect_common_issues(capture_result)

        # Should trigger critical issue with custom threshold (500)
        critical_issues = result.get_issues_by_severity("critical")
        size_issues = [i for i in critical_issues if "small" in i.description.lower()]
        assert len(size_issues) > 0

    @patch("textual_snapshots.detection.ET.fromstring")
    def test_xml_parsing_exception_handling(self, mock_fromstring, detector, temp_screenshot_dir):
        """Test handling of XML parsing exceptions."""
        # Mock XML parsing to raise exception
        mock_fromstring.side_effect = ET.ParseError("Mock parsing error")

        capture_result = self.create_mock_capture_result(
            svg_content="<invalid>xml</invalid>", temp_dir=temp_screenshot_dir
        )

        result = detector.detect_common_issues(capture_result)

        # Should handle exception gracefully and report parsing error
        critical_issues = result.get_issues_by_severity("critical")
        parse_issues = [i for i in critical_issues if "parsing error" in i.description.lower()]
        assert len(parse_issues) > 0

    def test_unicode_decode_error_handling(self, detector, temp_screenshot_dir):
        """Test handling of Unicode decode errors."""
        # Create file with binary content that can't be decoded as UTF-8
        screenshot_path = temp_screenshot_dir / "binary.svg"
        screenshot_path.write_bytes(b"\xff\xfe\x00\x00")  # Invalid UTF-8

        capture_result = self.create_mock_capture_result(
            screenshot_path=screenshot_path, file_size=4, temp_dir=temp_screenshot_dir
        )

        result = detector.detect_common_issues(capture_result)

        # Should handle encoding error gracefully
        critical_issues = result.get_issues_by_severity("critical")
        encoding_issues = [i for i in critical_issues if "encoding" in i.description.lower()]
        assert len(encoding_issues) > 0

    def test_general_exception_handling(self, detector, temp_screenshot_dir):
        """Test general exception handling during analysis."""
        # Create capture result with None path to trigger exception
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.screenshot_path = None  # Will cause issues in file operations
        mock_result.format = ScreenshotFormat.SVG
        mock_result.file_size_bytes = 1000
        mock_result.context = "test"

        result = detector.detect_common_issues(mock_result)

        # Should handle None path gracefully and return capture failure
        assert len(result.issues_detected) > 0
        capture_failure_issues = [
            i for i in result.issues_detected if i.category == "capture_failure"
        ]
        assert len(capture_failure_issues) > 0


class TestIssueDataclass:
    """Test Issue dataclass functionality."""

    def test_issue_creation(self):
        """Test Issue dataclass creation."""
        issue = Issue(
            category="test_category",
            description="Test description",
            severity="warning",
            confidence=0.8,
            suggestions=["Suggestion 1", "Suggestion 2"],
            metadata={"key": "value"},
        )

        assert issue.category == "test_category"
        assert issue.description == "Test description"
        assert issue.severity == "warning"
        assert issue.confidence == 0.8
        assert len(issue.suggestions) == 2
        assert issue.metadata["key"] == "value"

    def test_issue_defaults(self):
        """Test Issue dataclass with default values."""
        issue = Issue(category="test", description="Test", severity="info")

        assert issue.confidence == 0.0
        assert issue.suggestions == []
        assert issue.metadata == {}


class TestDetectionResultDataclass:
    """Test DetectionResult dataclass functionality."""

    def test_detection_result_creation(self):
        """Test DetectionResult creation."""
        issues = [
            Issue("test", "Critical issue", "critical"),
            Issue("test", "Warning issue", "warning"),
            Issue("test", "Info issue", "info"),
        ]

        result = DetectionResult(
            issues_detected=issues, detection_confidence=0.85, analysis_metadata={"test": True}
        )

        assert len(result.issues_detected) == 3
        assert result.detection_confidence == 0.85
        assert result.analysis_metadata["test"] is True
        assert isinstance(result.timestamp, datetime)

    def test_has_critical_issues_property(self):
        """Test has_critical_issues property."""
        # With critical issues
        critical_issues = [Issue("test", "Critical", "critical")]
        result = DetectionResult(critical_issues, 0.8)
        assert result.has_critical_issues is True

        # Without critical issues
        warning_issues = [Issue("test", "Warning", "warning")]
        result = DetectionResult(warning_issues, 0.8)
        assert result.has_critical_issues is False

    def test_has_warnings_property(self):
        """Test has_warnings property."""
        # With warnings
        warning_issues = [Issue("test", "Warning", "warning")]
        result = DetectionResult(warning_issues, 0.8)
        assert result.has_warnings is True

        # Without warnings
        info_issues = [Issue("test", "Info", "info")]
        result = DetectionResult(info_issues, 0.8)
        assert result.has_warnings is False

    def test_get_issues_by_severity(self):
        """Test filtering issues by severity."""
        issues = [
            Issue("test", "Critical issue", "critical"),
            Issue("test", "Warning issue", "warning"),
            Issue("test", "Another critical", "critical"),
            Issue("test", "Info issue", "info"),
        ]

        result = DetectionResult(issues, 0.8)

        critical_issues = result.get_issues_by_severity("critical")
        assert len(critical_issues) == 2

        warning_issues = result.get_issues_by_severity("warning")
        assert len(warning_issues) == 1

        info_issues = result.get_issues_by_severity("info")
        assert len(info_issues) == 1

        # Non-existent severity
        none_issues = result.get_issues_by_severity("nonexistent")
        assert len(none_issues) == 0
