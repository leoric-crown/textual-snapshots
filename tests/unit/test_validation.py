"""
Tests for external validation suite functionality.

Tests the algorithmic external validation system including:
- Multi-point reference validation
- Human baseline comparison
- Platform consistency validation
- Quality assessment metrics
- File similarity analysis
- SVG structure validation

Phase 2 testing from Enhanced PRP specification.
"""

import tempfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from textual_snapshots.capture import CaptureResult, ScreenshotFormat
from textual_snapshots.types import QualityMetrics, ValidationResult
from textual_snapshots.validation import ExternalValidationSuite


class TestExternalValidationSuite:
    """Test external validation suite functionality."""

    @pytest.fixture
    def temp_directories(self):
        """Create temporary directories for testing."""
        with tempfile.TemporaryDirectory() as base_dir:
            base_path = Path(base_dir)
            baseline_dir = base_path / "baselines"
            platform_dir = base_path / "platforms"
            screenshot_dir = base_path / "screenshots"

            # Create directories
            baseline_dir.mkdir(parents=True)
            platform_dir.mkdir(parents=True)
            screenshot_dir.mkdir(parents=True)

            yield {
                "baseline_dir": baseline_dir,
                "platform_dir": platform_dir,
                "screenshot_dir": screenshot_dir,
            }

    @pytest.fixture
    def validation_suite(self, temp_directories):
        """Create validation suite with temp directories."""
        return ExternalValidationSuite(
            baseline_directory=temp_directories["baseline_dir"],
            platform_reference_directory=temp_directories["platform_dir"],
        )

    @pytest.fixture
    def sample_svg_content(self):
        """Sample SVG content for testing."""
        return """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <rect x="10" y="10" width="30" height="30" style="fill:blue"/>
    <circle cx="70" cy="30" r="15" style="fill:red"/>
    <text x="20" y="70">Test Content</text>
    <path d="M20,80 L80,80" style="stroke:black"/>
</svg>"""

    @pytest.fixture
    def mock_capture_result(self, temp_directories, sample_svg_content):
        """Create mock capture result for testing."""
        screenshot_path = temp_directories["screenshot_dir"] / "test_screenshot.svg"
        screenshot_path.write_text(sample_svg_content)

        # Mock basic app context
        app_context = MagicMock()
        app_context.context_name = "test_app"
        app_context.app_id = "test_app_123"

        return CaptureResult(
            success=True,
            screenshot_path=screenshot_path,
            svg_path=screenshot_path,
            format=ScreenshotFormat.SVG,
            file_size_bytes=len(sample_svg_content),
            svg_size_bytes=len(sample_svg_content),
            context="test_context",
            app_context=app_context,
            timestamp=datetime.now(timezone.utc),
        )

    def test_initialization_with_defaults(self):
        """Test validation suite initialization with default parameters."""
        suite = ExternalValidationSuite()

        assert suite.baseline_directory == Path("baselines")
        assert suite.platform_reference_directory == Path("platform_refs")
        assert suite.quality_thresholds["file_size_min"] == 0.3
        assert suite.quality_thresholds["overall_min"] == 0.5

    def test_initialization_with_custom_parameters(self):
        """Test validation suite initialization with custom parameters."""
        custom_thresholds = {
            "file_size_min": 0.5,
            "content_complexity_min": 0.6,
            "structure_min": 0.7,
            "completeness_min": 0.8,
            "overall_min": 0.7,
        }

        suite = ExternalValidationSuite(
            baseline_directory=Path("custom_baselines"),
            quality_thresholds=custom_thresholds,
            platform_reference_directory=Path("custom_platforms"),
        )

        assert suite.baseline_directory == Path("custom_baselines")
        assert suite.platform_reference_directory == Path("custom_platforms")
        assert suite.quality_thresholds == custom_thresholds

    @pytest.mark.asyncio
    async def test_validate_against_references_failed_capture(self, validation_suite):
        """Test validation with failed capture result."""
        failed_result = CaptureResult(
            success=False,
            screenshot_path=None,
            context="failed_test",
            app_context=MagicMock(),
            error_message="Capture failed",
        )

        result = await validation_suite.validate_against_references(failed_result)

        assert not result.is_valid
        assert result.confidence == 0.0
        assert result.validation_type == "external_reference"
        assert "Screenshot capture failed" in result.issues[0]

    @pytest.mark.asyncio
    async def test_validate_against_references_successful(
        self, validation_suite, mock_capture_result
    ):
        """Test successful validation against references."""
        result = await validation_suite.validate_against_references(mock_capture_result)

        assert isinstance(result, ValidationResult)
        assert result.validation_type == "multi_point_external"
        assert "validation_breakdown" in result.metrics
        assert "individual_results" in result.metrics

        # Should have all three validation types
        breakdown = result.metrics["validation_breakdown"]
        assert "human_baseline" in breakdown
        assert "platform_consistency" in breakdown
        assert "quality_assessment" in breakdown

    @pytest.mark.asyncio
    async def test_compare_with_human_baselines_no_baseline(
        self, validation_suite, mock_capture_result
    ):
        """Test baseline comparison when no baseline files exist."""
        result = await validation_suite._compare_with_human_baselines(mock_capture_result)

        assert result.is_valid  # No baseline = no contradiction
        assert result.confidence == 0.3  # Low confidence
        assert result.validation_type == "human_baseline"
        assert "No human baseline found" in result.issues[0]
        assert result.metrics["baseline_files_found"] == 0

    @pytest.mark.asyncio
    async def test_compare_with_human_baselines_with_baselines(
        self, validation_suite, mock_capture_result, sample_svg_content, temp_directories
    ):
        """Test baseline comparison with existing baseline files."""
        # Create baseline files
        baseline1 = temp_directories["baseline_dir"] / "test_context_baseline_1.svg"
        baseline2 = temp_directories["baseline_dir"] / "test_context_baseline_2.svg"

        # Similar content for high similarity
        baseline1.write_text(sample_svg_content)
        baseline2.write_text(sample_svg_content.replace("blue", "green"))  # Slight variation

        result = await validation_suite._compare_with_human_baselines(mock_capture_result)

        assert isinstance(result, ValidationResult)
        assert result.validation_type == "human_baseline"
        assert result.metrics["baseline_files_found"] == 2
        assert "similarity_to_test_context_baseline_1.svg" in result.metrics
        assert "similarity_to_test_context_baseline_2.svg" in result.metrics
        assert "max_similarity" in result.metrics

    @pytest.mark.asyncio
    async def test_validate_platform_consistency_insufficient_refs(
        self, validation_suite, mock_capture_result
    ):
        """Test platform consistency validation with insufficient references."""
        result = await validation_suite._validate_platform_consistency(mock_capture_result)

        assert result.is_valid  # Cannot validate consistency
        assert result.confidence == 0.4  # Low confidence
        assert result.validation_type == "platform_consistency"
        assert "Insufficient platform references" in result.issues[0]

    @pytest.mark.asyncio
    async def test_validate_platform_consistency_with_refs(
        self, validation_suite, mock_capture_result, sample_svg_content, temp_directories
    ):
        """Test platform consistency validation with platform references."""
        # Create platform reference files
        platform1 = temp_directories["platform_dir"] / "test_context_platform_darwin_123.svg"
        platform2 = temp_directories["platform_dir"] / "test_context_platform_linux_123.svg"

        platform1.write_text(sample_svg_content)
        platform2.write_text(sample_svg_content.replace("Test Content", "Test Content Linux"))

        result = await validation_suite._validate_platform_consistency(mock_capture_result)

        assert isinstance(result, ValidationResult)
        assert result.validation_type == "platform_consistency"
        assert result.metrics["platform_count"] == 2
        assert "similarity_to_darwin" in result.metrics
        assert "similarity_to_linux" in result.metrics
        assert "consistency_variance" in result.metrics

    def test_assess_screenshot_quality_algorithmic_nonexistent_file(self, validation_suite):
        """Test quality assessment with nonexistent file."""
        mock_result = MagicMock()
        mock_result.screenshot_path = Path("nonexistent.svg")

        result = validation_suite._assess_screenshot_quality_algorithmic(mock_result)

        assert not result.is_valid
        assert result.confidence == 0.0
        assert result.validation_type == "quality_assessment"
        assert "does not exist" in result.issues[0]

    def test_assess_screenshot_quality_algorithmic_valid_file(
        self, validation_suite, mock_capture_result
    ):
        """Test quality assessment with valid file."""
        result = validation_suite._assess_screenshot_quality_algorithmic(mock_capture_result)

        assert isinstance(result, ValidationResult)
        assert result.validation_type == "quality_assessment"
        assert result.confidence >= 0.0
        assert result.confidence <= 1.0

        # Check that all expected metrics are present
        expected_metrics = [
            "file_size_score",
            "content_complexity_score",
            "structure_score",
            "completeness_score",
            "overall_score",
        ]
        for metric in expected_metrics:
            assert metric in result.metrics

    def test_calculate_file_similarity_identical_files(
        self, validation_suite, temp_directories, sample_svg_content
    ):
        """Test file similarity calculation with identical files."""
        file1 = temp_directories["screenshot_dir"] / "file1.svg"
        file2 = temp_directories["screenshot_dir"] / "file2.svg"

        file1.write_text(sample_svg_content)
        file2.write_text(sample_svg_content)

        similarity = validation_suite._calculate_file_similarity(file1, file2)
        assert similarity == 1.0

    def test_calculate_file_similarity_different_files(
        self, validation_suite, temp_directories, sample_svg_content
    ):
        """Test file similarity calculation with different files."""
        file1 = temp_directories["screenshot_dir"] / "file1.svg"
        file2 = temp_directories["screenshot_dir"] / "file2.svg"

        file1.write_text(sample_svg_content)
        file2.write_text(
            sample_svg_content.replace("blue", "red").replace("Test Content", "Different")
        )

        similarity = validation_suite._calculate_file_similarity(file1, file2)
        assert 0.0 <= similarity <= 1.0
        assert similarity < 1.0  # Should be less than identical

    def test_calculate_file_similarity_nonexistent_files(self, validation_suite):
        """Test file similarity with nonexistent files."""
        file1 = Path("nonexistent1.svg")
        file2 = Path("nonexistent2.svg")

        similarity = validation_suite._calculate_file_similarity(file1, file2)
        assert similarity == 0.0

    def test_calculate_svg_similarity_valid_files(
        self, validation_suite, temp_directories, sample_svg_content
    ):
        """Test SVG-specific similarity calculation."""
        file1 = temp_directories["screenshot_dir"] / "svg1.svg"
        file2 = temp_directories["screenshot_dir"] / "svg2.svg"

        # Create similar but not identical SVG content
        svg2_content = sample_svg_content.replace("blue", "green")

        file1.write_text(sample_svg_content)
        file2.write_text(svg2_content)

        similarity = validation_suite._calculate_svg_similarity(file1, file2)
        assert 0.0 <= similarity <= 1.0
        assert similarity > 0.7  # Should be high due to structural similarity

    def test_calculate_svg_similarity_invalid_svg(self, validation_suite, temp_directories):
        """Test SVG similarity with invalid SVG files."""
        file1 = temp_directories["screenshot_dir"] / "invalid1.svg"
        file2 = temp_directories["screenshot_dir"] / "invalid2.svg"

        file1.write_text("Not valid XML")
        file2.write_text("Also not valid XML")

        similarity = validation_suite._calculate_svg_similarity(file1, file2)
        assert 0.0 <= similarity <= 1.0  # Should fall back to size comparison

    def test_count_svg_elements(self, validation_suite, sample_svg_content):
        """Test SVG element counting functionality."""
        root = ET.fromstring(sample_svg_content)
        element_counts = validation_suite._count_svg_elements(root)

        assert element_counts["svg"] == 1
        assert element_counts["rect"] == 1
        assert element_counts["circle"] == 1
        assert element_counts["text"] == 1
        assert element_counts["path"] == 1

    def test_extract_platform_from_filename(self, validation_suite):
        """Test platform name extraction from filename."""
        filenames = [
            "test_context_platform_darwin_123.svg",
            "app_platform_linux_456.svg",
            "simple_platform_windows_789.svg",
            "no_platform_info.svg",
        ]

        expected = ["darwin", "linux", "windows", "unknown"]

        for filename, expected_platform in zip(filenames, expected):
            platform = validation_suite._extract_platform_from_filename(filename)
            assert platform == expected_platform

    def test_analyze_platform_consistency_empty_list(self, validation_suite):
        """Test platform consistency analysis with empty similarities."""
        result = validation_suite._analyze_platform_consistency([])

        assert result["variance"] == 1.0
        assert result["consistency_score"] == 0.0
        assert result["min_similarity"] == 0.0

    def test_analyze_platform_consistency_consistent_platforms(self, validation_suite):
        """Test platform consistency analysis with consistent platforms."""
        similarities = [0.9, 0.95, 0.92, 0.89]  # High, consistent similarities
        result = validation_suite._analyze_platform_consistency(similarities)

        assert result["variance"] < 0.1  # Low variance
        assert result["consistency_score"] > 0.8  # High consistency
        assert result["min_similarity"] > 0.8  # High minimum

    def test_analyze_platform_consistency_inconsistent_platforms(self, validation_suite):
        """Test platform consistency analysis with inconsistent platforms."""
        similarities = [0.9, 0.3, 0.8, 0.2]  # Mixed similarities
        result = validation_suite._analyze_platform_consistency(similarities)

        assert result["variance"] > 0.09  # Higher variance
        assert result["consistency_score"] < 0.5  # Lower consistency
        assert result["min_similarity"] == 0.2  # Low minimum


class TestQualityMetrics:
    """Test quality metrics functionality."""

    def test_quality_metrics_creation(self):
        """Test quality metrics data class creation."""
        metrics = QualityMetrics(
            file_size_score=0.8,
            content_complexity_score=0.7,
            structure_score=0.9,
            completeness_score=0.6,
            overall_score=0.75,
        )

        assert metrics.file_size_score == 0.8
        assert metrics.content_complexity_score == 0.7
        assert metrics.structure_score == 0.9
        assert metrics.completeness_score == 0.6
        assert metrics.overall_score == 0.75

    def test_quality_metrics_to_dict(self):
        """Test quality metrics conversion to dictionary."""
        metrics = QualityMetrics(
            file_size_score=0.8,
            content_complexity_score=0.7,
            structure_score=0.9,
            completeness_score=0.6,
            overall_score=0.75,
        )

        result = metrics.to_dict()

        assert isinstance(result, dict)
        assert result["file_size_score"] == 0.8
        assert result["content_complexity_score"] == 0.7
        assert result["structure_score"] == 0.9
        assert result["completeness_score"] == 0.6
        assert result["overall_score"] == 0.75


class TestValidationIntegration:
    """Test integration between validation components."""

    @pytest.fixture
    def validation_suite_with_files(self, tmp_path):
        """Create validation suite with test files."""
        baseline_dir = tmp_path / "baselines"
        platform_dir = tmp_path / "platforms"
        baseline_dir.mkdir()
        platform_dir.mkdir()

        # Create sample SVG content
        svg_content = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <rect x="10" y="10" width="30" height="30" style="fill:blue"/>
    <text x="20" y="70">Integration Test</text>
</svg>"""

        # Create baseline and platform reference files
        (baseline_dir / "integration_test_baseline_1.svg").write_text(svg_content)
        (platform_dir / "integration_test_platform_darwin_123.svg").write_text(svg_content)
        (platform_dir / "integration_test_platform_linux_456.svg").write_text(
            svg_content.replace("blue", "red")
        )

        return ExternalValidationSuite(
            baseline_directory=baseline_dir, platform_reference_directory=platform_dir
        )

    @pytest.mark.asyncio
    async def test_full_validation_workflow(self, validation_suite_with_files, tmp_path):
        """Test complete validation workflow with real files."""
        # Create test screenshot
        screenshot_path = tmp_path / "test_screenshot.svg"
        svg_content = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <rect x="10" y="10" width="30" height="30" style="fill:blue"/>
    <text x="20" y="70">Integration Test</text>
</svg>"""
        screenshot_path.write_text(svg_content)

        # Create capture result
        app_context = MagicMock()
        app_context.context_name = "integration_test"
        app_context.app_id = "integration_test_123"

        capture_result = CaptureResult(
            success=True,
            screenshot_path=screenshot_path,
            svg_path=screenshot_path,
            format=ScreenshotFormat.SVG,
            file_size_bytes=len(svg_content),
            svg_size_bytes=len(svg_content),
            context="integration_test",
            app_context=app_context,
            timestamp=datetime.now(timezone.utc),
        )

        # Run full validation
        result = await validation_suite_with_files.validate_against_references(capture_result)

        # Verify comprehensive validation result
        assert isinstance(result, ValidationResult)
        assert result.validation_type == "multi_point_external"
        assert "validation_breakdown" in result.metrics
        assert "individual_results" in result.metrics

        # Verify all validation types were executed
        breakdown = result.metrics["validation_breakdown"]
        assert len(breakdown) == 3
        assert all(0.0 <= confidence <= 1.0 for confidence in breakdown.values())

    def test_file_size_normalization_edge_cases(self, validation_suite_with_files):
        """Test file size score normalization with edge cases."""
        test_cases = [
            (0, 0.0),  # Empty file
            (1000, 0.0),  # Below minimum
            (2000, 0.0),  # At minimum
            (10000, 1.0),  # Optimal minimum
            (250000, 1.0),  # Optimal range
            (500000, 1.0),  # Optimal maximum
            (1000000, 0.6667),  # Above optimal
            (2000000, 0.0),  # At maximum
            (3000000, 0.0),  # Above maximum
        ]

        for file_size, expected_score in test_cases:
            score = validation_suite_with_files._normalize_file_size_score(file_size)
            assert abs(score - expected_score) < 0.1, (
                f"Size {file_size}: expected {expected_score}, got {score}"
            )

    def test_svg_structure_validation_edge_cases(self, validation_suite_with_files, tmp_path):
        """Test SVG structure validation with various edge cases."""
        test_cases = [
            # Valid SVG with all good features
            (
                """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <rect x="10" y="10" width="30" height="30"/>
</svg>""",
                1.0,
            ),
            # Valid SVG without viewBox
            (
                """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg">
    <rect x="10" y="10" width="30" height="30"/>
</svg>""",
                0.75,
            ),
            # Empty SVG
            (
                """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"/>""",
                0.5,
            ),
            # Invalid XML
            ("<svg>Not properly closed", 0.0),
        ]

        for i, (svg_content, expected_score) in enumerate(test_cases):
            svg_path = tmp_path / f"test_structure_{i}.svg"
            svg_path.write_text(svg_content)

            score = validation_suite_with_files._validate_svg_structure(svg_path)
            assert abs(score - expected_score) < 0.3, (
                f"Test case {i}: expected {expected_score}, got {score}"
            )
