"""
Interaction validation for textual-snapshots.

Implements comprehensive interaction format validation with LLM-friendly error messages
to address the #1 consumer friction point. Provides immediate, actionable feedback for
interaction format mistakes with examples and fix suggestions.
"""

from abc import ABC, abstractmethod
from typing import Literal, Union

from pydantic import BaseModel


class InteractionValidationError(Exception):
    """Custom exception for interaction validation errors with LLM-friendly context."""

    def __init__(self, message: str, suggestions: list[str], examples: list[str]):
        self.message = message
        self.suggestions = suggestions
        self.examples = examples
        super().__init__(message)

    def to_dict(self) -> dict[str, Union[str, list[str]]]:
        """Convert to dictionary for structured error reporting."""
        return {"message": self.message, "suggestions": self.suggestions, "examples": self.examples}


class BaseInteraction(BaseModel, ABC):
    """Base class for all interaction types with validation."""

    @abstractmethod
    def to_command(self) -> str:
        """Convert to command string format."""
        pass

    @classmethod
    @abstractmethod
    def get_examples(cls) -> list[str]:
        """Get example usage for error messages."""
        pass


class PressInteraction(BaseInteraction):
    """Key press interaction validation."""

    type: Literal["press"] = "press"
    key: str

    def to_command(self) -> str:
        return f"press:{self.key}"

    @classmethod
    def get_examples(cls) -> list[str]:
        return ["press:f2", "press:enter", "press:escape", "press:ctrl+c"]


class ClickInteraction(BaseInteraction):
    """Click interaction validation."""

    type: Literal["click"] = "click"
    selector: str

    def to_command(self) -> str:
        return f"click:{self.selector}"

    @classmethod
    def get_examples(cls) -> list[str]:
        return ["click:#button", "click:.submit", "click:Button"]


class HoverInteraction(BaseInteraction):
    """Hover interaction validation."""

    type: Literal["hover"] = "hover"
    selector: str

    def to_command(self) -> str:
        return f"hover:{self.selector}"

    @classmethod
    def get_examples(cls) -> list[str]:
        return ["hover:#menu", "hover:.dropdown", "hover:Button"]


class TypeInteraction(BaseInteraction):
    """Text typing interaction validation."""

    type: Literal["type"] = "type"
    text: str

    def to_command(self) -> str:
        return f"type:{self.text}"

    @classmethod
    def get_examples(cls) -> list[str]:
        return ["type:hello world", "type:username", "type:password123"]


class WaitInteraction(BaseInteraction):
    """Wait/delay interaction validation."""

    type: Literal["wait"] = "wait"
    duration: float

    def to_command(self) -> str:
        return f"wait:{self.duration}"

    @classmethod
    def get_examples(cls) -> list[str]:
        return ["wait:0.5", "wait:1.0", "wait:2.0"]


class ValidationResult(BaseModel):
    """Result of interaction validation with LLM-friendly context."""

    is_valid: bool
    validated_interactions: list[str] = []
    errors: list[dict[str, Union[str, int, list[str]]]] = []  # Store error dictionaries instead of exceptions
    suggestions: list[str] = []


class InteractionValidator:
    """Validates and parses interaction sequences with LLM-friendly errors."""

    @classmethod
    def parse_interaction(cls, interaction_string: str, index: int = 0) -> str:
        """
        Parse single interaction with comprehensive error handling.

        Returns the original string if valid (for backward compatibility).
        Raises InteractionValidationError with detailed guidance if invalid.
        """
        if not isinstance(interaction_string, str):
            raise InteractionValidationError(
                f"Interaction must be string, got {type(interaction_string).__name__}",
                ["Convert to string format", "Use proper interaction syntax"],
                ["press:f2", "click:#button", "wait:1.0"],
            )

        if ":" not in interaction_string:
            # CRITICAL: This is the #1 user mistake - provide detailed guidance
            raise InteractionValidationError(
                f"Interaction '{interaction_string}' missing required ':' separator. "
                f"All interactions must use 'type:target' format.",
                [
                    f"Change '{interaction_string}' to 'press:{interaction_string}' for key presses",
                    f"Change '{interaction_string}' to 'click:#{interaction_string}' for element clicks by ID",
                    f"Change '{interaction_string}' to 'click:{interaction_string}' for CSS selectors",
                    "Use 'type:text' for text input",
                    "Use 'wait:seconds' for delays",
                ],
                [
                    f"press:{interaction_string}  # if this is a key press",
                    f"click:#{interaction_string}  # if this is an element ID",
                    f"click:.{interaction_string}  # if this is a CSS class",
                    f"click:{interaction_string}  # if this is a CSS selector",
                ],
            )

        action_type, target = interaction_string.split(":", 1)

        # Validate based on interaction type with specific guidance
        if action_type == "press":
            # Basic validation - ensure key is not empty
            if not target.strip():
                raise InteractionValidationError(
                    "Press action missing key name",
                    ["Specify which key to press", "Common keys: enter, f2, escape, ctrl+c"],
                    ["press:enter", "press:f2", "press:escape", "press:ctrl+c"],
                )
        elif action_type == "click":
            # Basic validation - ensure selector is not empty
            if not target.strip():
                raise InteractionValidationError(
                    "Click action missing selector",
                    ["Specify element selector", "Use #id, .class, or element name"],
                    ["click:#button", "click:.submit", "click:Button"],
                )
        elif action_type == "hover":
            # Basic validation - ensure selector is not empty
            if not target.strip():
                raise InteractionValidationError(
                    "Hover action missing selector",
                    ["Specify element selector", "Use #id, .class, or element name"],
                    ["hover:#menu", "hover:.dropdown", "hover:Button"],
                )
        elif action_type == "type":
            # Basic validation - allow empty text (might be intentional)
            pass
        elif action_type == "wait":
            try:
                duration = float(target)
                if duration < 0:
                    raise InteractionValidationError(
                        f"Wait duration cannot be negative: {duration}",
                        [
                            "Use positive numbers for wait times",
                            "Common values: 0.1, 0.5, 1.0, 2.0",
                        ],
                        ["wait:0.5", "wait:1.0", "wait:2.0"],
                    )
            except ValueError as e:
                raise InteractionValidationError(
                    f"Wait duration '{target}' must be a number",
                    ["Use decimal numbers for wait times", "Common values: 0.1, 0.5, 1.0, 2.0"],
                    ["wait:0.5", "wait:1.0", "wait:2.0"],
                ) from e
        else:
            raise InteractionValidationError(
                f"Unknown interaction type '{action_type}'",
                [
                    "Use 'press:' for keyboard interactions",
                    "Use 'click:' for mouse clicks",
                    "Use 'hover:' for hover actions",
                    "Use 'type:' for text input",
                    "Use 'wait:' for delays",
                ],
                [
                    "press:enter",
                    "click:#button",
                    "hover:.menu-item",
                    "type:hello world",
                    "wait:1.0",
                ],
            )

        # Return original string for backward compatibility
        return interaction_string

    @classmethod
    def validate_sequence(cls, interactions: list[str]) -> ValidationResult:
        """
        Validate entire interaction sequence with comprehensive feedback.

        Returns ValidationResult with detailed error information for LLM consumption.
        """
        validated = []
        errors = []
        suggestions = []

        for i, interaction in enumerate(interactions):
            try:
                validated_interaction = cls.parse_interaction(interaction, i)
                validated.append(validated_interaction)
            except InteractionValidationError as e:
                errors.append({"index": i, "interaction": interaction, **e.to_dict()})

        # Provide sequence-level suggestions
        if errors:
            suggestions.extend(
                [
                    "Check the interaction format documentation for examples",
                    "All interactions must use 'type:target' format with colon separator",
                    "Common mistake: using bare strings instead of prefixed format",
                    f"Found {len(errors)} format error(s) in {len(interactions)} interaction(s)",
                ]
            )

        return ValidationResult(
            is_valid=len(errors) == 0,
            validated_interactions=validated,
            errors=errors,
            suggestions=suggestions,
        )

    @classmethod
    def format_validation_errors(cls, validation_result: ValidationResult) -> str:
        """
        Format validation errors into LLM-friendly error message.

        Returns a comprehensive error message with examples and suggestions.
        """
        if validation_result.is_valid:
            return ""

        error_parts = ["❌ Interaction Format Errors:"]

        for error in validation_result.errors:
            # Type-safe access to error dictionary values
            index_val = error.get('index', 0)
            message = error.get('message', 'Unknown error')
            interaction = error.get('interaction', '')
            suggestions = error.get('suggestions', [])
            examples = error.get('examples', [])

            # Ensure index is an integer for safe arithmetic
            index = int(index_val) if isinstance(index_val, (int, str)) else 0
            error_parts.append(f"\n  Error at position {index + 1}: {message}")
            error_parts.append(f"    Invalid: '{interaction}'")

            # Ensure we have a list of suggestions
            if isinstance(suggestions, list):
                for suggestion in suggestions:
                    error_parts.append(f"    💡 {suggestion}")

            error_parts.append("    ✅ Examples:")
            # Ensure we have a list of examples
            if isinstance(examples, list):
                for example in examples:
                    error_parts.append(f"       {example}")

        # Add general suggestions
        if validation_result.suggestions:
            error_parts.append("\n💡 General Suggestions:")
            for suggestion in validation_result.suggestions:
                error_parts.append(f"   • {suggestion}")

        return "".join(error_parts)
