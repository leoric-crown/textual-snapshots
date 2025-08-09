"""
Comprehensive tests for interaction validation system.

Tests focus on behavioral validation and LLM-friendly error messages for the
interaction validation system that addresses the #1 consumer friction point.
Covers common user mistakes, error message quality, and integration scenarios.
"""


import pytest

from textual_snapshots.capture import ScreenshotCapture
from textual_snapshots.interactions import (
    ClickInteraction,
    HoverInteraction,
    InteractionValidationError,
    InteractionValidator,
    PressInteraction,
    TypeInteraction,
    ValidationResult,
    WaitInteraction,
)


class TestInteractionValidationError:
    """Test the custom validation error class."""

    def test_initialization(self):
        """Test error initialization with all components."""
        error = InteractionValidationError(
            message="Test error",
            suggestions=["Fix 1", "Fix 2"],
            examples=["example:1", "example:2"],
        )

        assert error.message == "Test error"
        assert error.suggestions == ["Fix 1", "Fix 2"]
        assert error.examples == ["example:1", "example:2"]
        assert str(error) == "Test error"

    def test_to_dict(self):
        """Test error serialization to dictionary."""
        error = InteractionValidationError(
            message="Format error", suggestions=["Use colon separator"], examples=["press:enter"]
        )

        result = error.to_dict()
        expected = {
            "message": "Format error",
            "suggestions": ["Use colon separator"],
            "examples": ["press:enter"],
        }
        assert result == expected


class TestInteractionModels:
    """Test the Pydantic interaction model classes."""

    def test_press_interaction(self):
        """Test press interaction model."""
        press = PressInteraction(key="enter")
        assert press.type == "press"
        assert press.key == "enter"
        assert press.to_command() == "press:enter"
        assert len(press.get_examples()) > 0
        assert "press:f2" in press.get_examples()

    def test_click_interaction(self):
        """Test click interaction model."""
        click = ClickInteraction(selector="#button")
        assert click.type == "click"
        assert click.selector == "#button"
        assert click.to_command() == "click:#button"
        assert "click:#button" in click.get_examples()

    def test_hover_interaction(self):
        """Test hover interaction model."""
        hover = HoverInteraction(selector=".menu")
        assert hover.type == "hover"
        assert hover.selector == ".menu"
        assert hover.to_command() == "hover:.menu"
        assert "hover:#menu" in hover.get_examples()

    def test_type_interaction(self):
        """Test type interaction model."""
        type_interaction = TypeInteraction(text="hello world")
        assert type_interaction.type == "type"
        assert type_interaction.text == "hello world"
        assert type_interaction.to_command() == "type:hello world"
        assert "type:hello world" in type_interaction.get_examples()

    def test_wait_interaction(self):
        """Test wait interaction model."""
        wait = WaitInteraction(duration=1.5)
        assert wait.type == "wait"
        assert wait.duration == 1.5
        assert wait.to_command() == "wait:1.5"
        assert "wait:0.5" in wait.get_examples()


class TestInteractionValidatorParseInteraction:
    """Test the parse_interaction method with all error scenarios."""

    def test_valid_interactions_unchanged(self):
        """Test that valid interactions pass through unchanged."""
        valid_interactions = [
            "press:enter",
            "press:f2",
            "press:ctrl+c",
            "click:#button",
            "click:.submit",
            "click:Button",
            "hover:#menu",
            "hover:.dropdown",
            "type:hello world",
            "type:",  # Empty text is allowed
            "wait:0.5",
            "wait:1.0",
            "wait:2.0",
        ]

        for interaction in valid_interactions:
            result = InteractionValidator.parse_interaction(interaction)
            assert result == interaction, f"Valid interaction was modified: {interaction}"

    def test_non_string_input_error(self):
        """Test error for non-string input."""
        with pytest.raises(InteractionValidationError) as exc_info:
            InteractionValidator.parse_interaction(123)

        error = exc_info.value
        assert "must be string" in error.message
        assert "got int" in error.message
        assert "Convert to string format" in error.suggestions
        assert len(error.examples) > 0

    def test_missing_colon_separator_error(self):
        """Test the #1 user mistake - missing colon separator."""
        # This is the critical test case - most common user error
        problematic_inputs = ["f2", "button", "enter", "click_me"]

        for input_str in problematic_inputs:
            with pytest.raises(InteractionValidationError) as exc_info:
                InteractionValidator.parse_interaction(input_str)

            error = exc_info.value
            assert "missing required ':' separator" in error.message
            assert input_str in error.message
            assert "type:target" in error.message

            # Verify helpful suggestions are provided
            assert any(f"press:{input_str}" in suggestion for suggestion in error.suggestions)
            assert any(f"click:#{input_str}" in suggestion for suggestion in error.suggestions)

            # Verify examples show proper format
            assert any(f"press:{input_str}" in example for example in error.examples)
            assert any(f"click:#{input_str}" in example for example in error.examples)

    def test_press_empty_key_error(self):
        """Test press action with empty key."""
        with pytest.raises(InteractionValidationError) as exc_info:
            InteractionValidator.parse_interaction("press:")

        error = exc_info.value
        assert "Press action missing key name" in error.message
        assert "Specify which key to press" in error.suggestions
        assert "press:enter" in error.examples

    def test_click_empty_selector_error(self):
        """Test click action with empty selector."""
        with pytest.raises(InteractionValidationError) as exc_info:
            InteractionValidator.parse_interaction("click:")

        error = exc_info.value
        assert "Click action missing selector" in error.message
        assert "Use #id, .class, or element name" in error.suggestions
        assert "click:#button" in error.examples

    def test_hover_empty_selector_error(self):
        """Test hover action with empty selector."""
        with pytest.raises(InteractionValidationError) as exc_info:
            InteractionValidator.parse_interaction("hover:")

        error = exc_info.value
        assert "Hover action missing selector" in error.message
        assert "Use #id, .class, or element name" in error.suggestions
        assert "hover:#menu" in error.examples

    def test_wait_invalid_duration_error(self):
        """Test wait action with invalid duration."""
        invalid_durations = ["wait:abc", "wait:not_a_number", "wait:"]

        for interaction in invalid_durations:
            with pytest.raises(InteractionValidationError) as exc_info:
                InteractionValidator.parse_interaction(interaction)

            error = exc_info.value
            assert "must be a number" in error.message
            assert "Use decimal numbers for wait times" in error.suggestions
            assert "wait:0.5" in error.examples

    def test_wait_negative_duration_error(self):
        """Test wait action with negative duration."""
        with pytest.raises(InteractionValidationError) as exc_info:
            InteractionValidator.parse_interaction("wait:-1.0")

        error = exc_info.value
        assert "cannot be negative" in error.message
        assert "Use positive numbers for wait times" in error.suggestions
        assert "wait:1.0" in error.examples

    def test_unknown_action_type_error(self):
        """Test unknown action type."""
        unknown_actions = ["invalid:target", "unknown:selector", "badaction:value"]

        for interaction in unknown_actions:
            with pytest.raises(InteractionValidationError) as exc_info:
                InteractionValidator.parse_interaction(interaction)

            error = exc_info.value
            action_type = interaction.split(":")[0]
            assert f"Unknown interaction type '{action_type}'" in error.message

            # Verify comprehensive suggestions
            assert "Use 'press:' for keyboard interactions" in error.suggestions
            assert "Use 'click:' for mouse clicks" in error.suggestions
            assert "Use 'hover:' for hover actions" in error.suggestions
            assert "Use 'type:' for text input" in error.suggestions
            assert "Use 'wait:' for delays" in error.suggestions

            # Verify examples for all interaction types
            assert "press:enter" in error.examples
            assert "click:#button" in error.examples
            assert "type:hello world" in error.examples
            assert "wait:1.0" in error.examples

    def test_type_allows_empty_text(self):
        """Test that type interaction allows empty text (might be intentional)."""
        # This should NOT raise an error - empty text might be intentional
        result = InteractionValidator.parse_interaction("type:")
        assert result == "type:"


class TestInteractionValidatorSequenceValidation:
    """Test the validate_sequence method for batch validation."""

    def test_valid_sequence_passes(self):
        """Test that valid interaction sequence passes validation."""
        valid_sequence = [
            "press:f2",
            "click:#button",
            "type:hello world",
            "hover:.menu",
            "wait:1.0",
        ]

        result = InteractionValidator.validate_sequence(valid_sequence)
        assert result.is_valid is True
        assert result.validated_interactions == valid_sequence
        assert len(result.errors) == 0
        assert len(result.suggestions) == 0

    def test_mixed_valid_invalid_sequence(self):
        """Test sequence with both valid and invalid interactions."""
        mixed_sequence = [
            "press:f2",  # Valid
            "button",  # Invalid - missing colon
            "click:#submit",  # Valid
            "invalid:target",  # Invalid - unknown type
            "wait:1.0",  # Valid
        ]

        result = InteractionValidator.validate_sequence(mixed_sequence)
        assert result.is_valid is False
        assert len(result.errors) == 2
        # Validation continues through the sequence, so valid interactions still get validated
        assert len(result.validated_interactions) == 3  # Valid interactions that passed

        # Check first error (missing colon)
        error1 = result.errors[0]
        assert error1["index"] == 1
        assert error1["interaction"] == "button"
        assert "missing required ':' separator" in error1["message"]

        # Check second error (unknown type)
        error2 = result.errors[1]
        assert error2["index"] == 3
        assert error2["interaction"] == "invalid:target"
        assert "Unknown interaction type 'invalid'" in error2["message"]

    def test_empty_sequence_valid(self):
        """Test that empty sequence is valid."""
        result = InteractionValidator.validate_sequence([])
        assert result.is_valid is True
        assert len(result.validated_interactions) == 0
        assert len(result.errors) == 0

    def test_all_invalid_sequence(self):
        """Test sequence where all interactions are invalid."""
        invalid_sequence = [
            "f2",  # Missing colon
            "press:",  # Empty key
            "invalid:target",  # Unknown type
        ]

        result = InteractionValidator.validate_sequence(invalid_sequence)
        assert result.is_valid is False
        assert len(result.errors) == 3
        assert len(result.validated_interactions) == 0

        # Verify sequence-level suggestions are provided
        assert len(result.suggestions) > 0
        assert "Check the interaction format documentation for examples" in result.suggestions
        # Check that 'type:target' format guidance is in one of the suggestions
        suggestions_text = " ".join(result.suggestions)
        assert "type:target" in suggestions_text
        assert "Found 3 format error(s) in 3 interaction(s)" in result.suggestions

    def test_error_index_tracking(self):
        """Test that error indices are correctly tracked."""
        sequence = [
            "press:enter",  # Valid - index 0
            "invalid1",  # Invalid - index 1
            "click:#button",  # Valid - index 2
            "invalid2",  # Invalid - index 3
            "wait:1.0",  # Valid - index 4
        ]

        result = InteractionValidator.validate_sequence(sequence)
        assert result.is_valid is False
        assert len(result.errors) == 2

        assert result.errors[0]["index"] == 1
        assert result.errors[0]["interaction"] == "invalid1"
        assert result.errors[1]["index"] == 3
        assert result.errors[1]["interaction"] == "invalid2"


class TestErrorMessageFormatting:
    """Test LLM-friendly error message formatting."""

    def test_format_valid_result(self):
        """Test formatting when validation passes."""
        valid_result = ValidationResult(is_valid=True, validated_interactions=["press:f2"])
        formatted = InteractionValidator.format_validation_errors(valid_result)
        assert formatted == ""

    def test_format_single_error(self):
        """Test formatting with single validation error."""
        error_data = {
            "index": 0,
            "interaction": "f2",
            "message": "Missing colon separator",
            "suggestions": ["Use press:f2", "Use click:#f2"],
            "examples": ["press:f2", "click:#f2"],
        }

        result = ValidationResult(
            is_valid=False, errors=[error_data], suggestions=["Check format documentation"]
        )

        formatted = InteractionValidator.format_validation_errors(result)

        # Verify structure includes all components
        assert "❌ Interaction Format Errors:" in formatted
        assert "Error at position 1: Missing colon separator" in formatted
        assert "Invalid: 'f2'" in formatted
        assert "💡 Use press:f2" in formatted
        assert "✅ Examples:" in formatted
        assert "press:f2" in formatted
        assert "💡 General Suggestions:" in formatted
        assert "Check format documentation" in formatted

    def test_format_multiple_errors(self):
        """Test formatting with multiple validation errors."""
        errors = [
            {
                "index": 0,
                "interaction": "f2",
                "message": "Missing colon separator",
                "suggestions": ["Use press:f2"],
                "examples": ["press:f2"],
            },
            {
                "index": 2,
                "interaction": "press:",
                "message": "Empty key name",
                "suggestions": ["Specify key name"],
                "examples": ["press:enter"],
            },
        ]

        result = ValidationResult(
            is_valid=False, errors=errors, suggestions=["Multiple format errors found"]
        )

        formatted = InteractionValidator.format_validation_errors(result)

        # Verify both errors are formatted
        assert "Error at position 1:" in formatted
        assert "Error at position 3:" in formatted
        assert "Invalid: 'f2'" in formatted
        assert "Invalid: 'press:'" in formatted
        assert formatted.count("💡") >= 3  # At least 3 suggestion markers
        assert formatted.count("✅ Examples:") == 2  # One per error

    def test_llm_friendly_structure(self):
        """Test that formatted errors are optimized for LLM consumption."""
        error_data = {
            "index": 0,
            "interaction": "button",
            "message": "Interaction 'button' missing required ':' separator",
            "suggestions": [
                "Change 'button' to 'press:button' for key presses",
                "Change 'button' to 'click:#button' for element clicks by ID",
            ],
            "examples": [
                "press:button  # if this is a key press",
                "click:#button  # if this is an element ID",
            ],
        }

        result = ValidationResult(is_valid=False, errors=[error_data])
        formatted = InteractionValidator.format_validation_errors(result)

        # Verify LLM-friendly characteristics
        assert "❌" in formatted  # Clear visual indicators
        assert "💡" in formatted  # Suggestion markers
        assert "✅" in formatted  # Example markers
        assert "Error at position 1:" in formatted  # Clear position reference
        assert "# if this is" in formatted  # Explanatory comments in examples


class TestCaptureIntegration:
    """Test integration with the capture system."""

    @pytest.mark.asyncio
    async def test_perform_interactions_validation_success(self, mock_pilot, temp_screenshots_dir):
        """Test that _perform_interactions validates interactions before execution."""
        capture = ScreenshotCapture(base_directory=temp_screenshots_dir)

        valid_interactions = ["press:f2", "click:#button", "wait:1.0"]

        # Should not raise - validation passes
        await capture._perform_interactions(mock_pilot, valid_interactions)

        # Verify interactions were executed
        mock_pilot.press.assert_called_once_with("f2")
        mock_pilot.click.assert_called_once_with("#button")

    @pytest.mark.asyncio
    async def test_perform_interactions_validation_failure(self, mock_pilot, temp_screenshots_dir):
        """Test that _perform_interactions fails on invalid interactions."""
        capture = ScreenshotCapture(base_directory=temp_screenshots_dir)

        invalid_interactions = ["f2", "click:", "invalid:target"]  # Multiple errors

        with pytest.raises(ValueError) as exc_info:
            await capture._perform_interactions(mock_pilot, invalid_interactions)

        # Verify comprehensive error message
        error_message = str(exc_info.value)
        assert "Invalid interaction format" in error_message
        assert "❌ Interaction Format Errors:" in error_message
        assert "missing required ':' separator" in error_message
        assert "💡" in error_message  # Suggestions included

        # Verify no interactions were executed
        mock_pilot.press.assert_not_called()
        mock_pilot.click.assert_not_called()

    @pytest.mark.asyncio
    async def test_validation_preserves_existing_behavior(self, mock_pilot, temp_screenshots_dir):
        """Test that validation doesn't break existing interaction processing."""
        capture = ScreenshotCapture(base_directory=temp_screenshots_dir)

        # Test all supported interaction types
        interactions = [
            "press:enter",
            "click:#submit",
            "hover:.menu",
            "type:hello world",
            "wait:0.5",
        ]

        await capture._perform_interactions(mock_pilot, interactions)

        # Verify all interactions were processed correctly
        mock_pilot.press.assert_any_call("enter")
        mock_pilot.click.assert_any_call("#submit")
        mock_pilot.hover.assert_any_call(".menu")
        # type is implemented as individual character presses
        assert mock_pilot.press.call_count > 1  # Multiple calls for typing


class TestPerformanceAndCompatibility:
    """Test performance and backward compatibility requirements."""

    def test_validation_performance(self):
        """Test that validation is fast enough for development workflows."""
        import time

        # Large sequence to test performance
        large_sequence = ["press:f2", "click:#button", "wait:1.0"] * 100

        start_time = time.time()
        result = InteractionValidator.validate_sequence(large_sequence)
        end_time = time.time()

        assert result.is_valid is True
        assert (end_time - start_time) < 0.1  # Should complete in under 100ms

    def test_backward_compatibility_preserved(self):
        """Test that all existing valid formats continue to work."""
        # Comprehensive list of formats that should remain valid
        existing_formats = [
            "press:enter",
            "press:f1",
            "press:f12",
            "press:ctrl+c",
            "press:ctrl+shift+p",
            "click:#id",
            "click:.class",
            "click:button",
            "click:input[type=submit]",
            "hover:#menu",
            "hover:.dropdown",
            "type:simple text",
            "type:complex text with spaces and symbols!@#",
            "type:",  # Empty text
            "wait:0",
            "wait:0.1",
            "wait:1.0",
            "wait:10.5",
        ]

        for interaction in existing_formats:
            # Should not raise any exception
            result = InteractionValidator.parse_interaction(interaction)
            assert result == interaction, f"Existing format was modified: {interaction}"

    def test_edge_cases_handling(self):
        """Test handling of edge cases and unusual inputs."""
        # These edge cases should pass validation
        edge_cases = [
            "press:x",  # Single character key (valid)
            "click: #button",  # Space before selector
            "type:\n",  # Newline character
            "wait:0.0",  # Zero wait (valid)
        ]

        for interaction in edge_cases:
            # Should not raise any exception
            result = InteractionValidator.parse_interaction(interaction)
            assert result == interaction

    def test_memory_efficiency(self):
        """Test that validation doesn't consume excessive memory."""
        import sys

        # Create validation result with many errors
        large_error_list = []
        for i in range(1000):
            large_error_list.append(
                {
                    "index": i,
                    "interaction": f"invalid{i}",
                    "message": f"Error {i}",
                    "suggestions": [f"Fix {i}"],
                    "examples": [f"example{i}:value"],
                }
            )

        result = ValidationResult(
            is_valid=False, errors=large_error_list, suggestions=["General suggestion"]
        )

        # Memory usage should be reasonable (rough check)
        size = sys.getsizeof(result)
        assert size < 1_000_000  # Less than 1MB for 1000 errors


class TestValidationResultModel:
    """Test the ValidationResult Pydantic model."""

    def test_validation_result_initialization(self):
        """Test ValidationResult model initialization."""
        result = ValidationResult(
            is_valid=False,
            validated_interactions=["press:f2"],
            errors=[{"index": 1, "message": "test error"}],
            suggestions=["test suggestion"],
        )

        assert result.is_valid is False
        assert result.validated_interactions == ["press:f2"]
        assert len(result.errors) == 1
        assert result.suggestions == ["test suggestion"]

    def test_validation_result_defaults(self):
        """Test ValidationResult default values."""
        result = ValidationResult(is_valid=True)

        assert result.is_valid is True
        assert result.validated_interactions == []
        assert result.errors == []
        assert result.suggestions == []

    def test_validation_result_serialization(self):
        """Test that ValidationResult can be serialized (important for API usage)."""
        result = ValidationResult(
            is_valid=False,
            validated_interactions=["press:f2"],
            errors=[{"index": 0, "message": "test"}],
            suggestions=["fix it"],
        )

        # Should be able to convert to dict
        dict_result = result.model_dump()
        assert isinstance(dict_result, dict)
        assert dict_result["is_valid"] is False
        assert dict_result["validated_interactions"] == ["press:f2"]


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v"])
