"""
Type definitions and protocols for textual-snapshots.

Defines core protocols and types used throughout the package
to avoid circular import issues while maintaining clean interfaces.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol

from textual.app import App


class AppContext(Protocol):
    """
    Generic application context protocol for screenshot capture.

    Replaces SessionManager dependency with generic interface that works
    with any Textual application while maintaining compatibility with
    existing session-aware applications.
    """

    @property
    def app_id(self) -> str:
        """Unique application identifier for caching and organization."""

    @property
    def context_name(self) -> str:
        """Human-readable context name for organization and display."""

    def get_state_hash(self) -> str:
        """Generate hash representing current application state for caching."""

    def get_metadata(self) -> dict[str, Any]:
        """Get rich metadata for AI-ready context collection."""

    def get_app_instance(self) -> App[Any]:
        """Return the Textual app instance to capture."""


# Validation System Types


@dataclass
class ValidationResult:
    """Result of external validation operation."""

    is_valid: bool
    confidence: float  # 0.0 to 1.0
    validation_type: str
    issues: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class QualityMetrics:
    """Algorithmic quality assessment metrics."""

    file_size_score: float  # 0.0 to 1.0
    content_complexity_score: float  # 0.0 to 1.0
    structure_score: float  # 0.0 to 1.0
    completeness_score: float  # 0.0 to 1.0
    overall_score: float  # 0.0 to 1.0

    def to_dict(self) -> dict[str, float]:
        """Convert metrics to dictionary format."""
        return {
            "file_size_score": self.file_size_score,
            "content_complexity_score": self.content_complexity_score,
            "structure_score": self.structure_score,
            "completeness_score": self.completeness_score,
            "overall_score": self.overall_score,
        }


@dataclass
class PlatformConsistency:
    """Platform consistency validation results."""

    consistent: bool
    platform_scores: dict[str, float]  # Platform -> consistency score
    inconsistencies: list[str]
    cross_platform_score: float  # 0.0 to 1.0
