"""
textual-snapshots: Professional visual testing for Textual applications.

This package provides comprehensive screenshot capture and visual testing capabilities
for Textual applications, with plugin extensibility and AI-ready architecture.
"""

from .capture import (
    BasicAppContext,
    CaptureResult,
    ScreenshotCapture,
    ScreenshotFormat,
    capture_app_screenshot,
)
from .detection import (
    DetectionResult,
    Issue,
    ProactiveErrorDetector,
)
from .interactions import (
    InteractionValidationError,
    InteractionValidator,
)
from .interactions import (
    ValidationResult as InteractionValidationResult,
)
from .plugins import CapturePlugin
from .types import AppContext, QualityMetrics, ValidationResult
from .validation import ExternalValidationSuite

__version__ = "0.1.0"
__author__ = "Testinator Team"
__email__ = "team@testinator.dev"

__all__ = [
    # Core classes
    "ScreenshotCapture",
    "CaptureResult",
    "BasicAppContext",
    "AppContext",
    "ScreenshotFormat",
    # Main functions
    "capture_app_screenshot",
    # Plugin system
    "CapturePlugin",
    # Validation system
    "ExternalValidationSuite",
    "ValidationResult",
    "QualityMetrics",
    # Interaction validation
    "InteractionValidator",
    "InteractionValidationError",
    "InteractionValidationResult",
    # Detection system
    "ProactiveErrorDetector",
    "DetectionResult",
    "Issue",
]
