#!/usr/bin/env python3
"""
Interaction Validation Demo for textual-snapshots.

Demonstrates the enhanced interaction validation system that addresses the #1 consumer
friction point - interaction format mistakes that previously failed silently.

This example shows:
1. Common interaction format mistakes and their helpful error messages
2. LLM-friendly error structure with examples and fix suggestions
3. Backward compatibility with existing valid interaction patterns
4. How validation integrates with capture operations
"""

import asyncio

from textual.app import App
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Static

# Import the validation system
from textual_snapshots import (
    InteractionValidator,
    capture_app_screenshot,
)


class ValidationDemoApp(App[None]):
    """Simple demo app for testing interaction validation."""

    def compose(self):
        """Create the app layout."""
        yield Vertical(
            Static("Interaction Validation Demo", classes="title"),
            Horizontal(
                Button("Demo Button", id="demo-button"),
                Button("Another Button", id="another-button"),
                classes="buttons"
            ),
            Static("Click buttons to test interactions", classes="instructions"),
            classes="container"
        )


def demo_common_mistakes():
    """Demonstrate common interaction format mistakes and their helpful error messages."""
    print("🔍 Interaction Validation Demo")
    print("=" * 50)

    # Common mistake examples from real user feedback
    mistake_examples = [
        {
            "name": "Missing Colon Separator (#1 User Mistake)",
            "interactions": ["f2", "button", "enter"],
            "explanation": "Users expect bare strings to work"
        },
        {
            "name": "Invalid Action Type",
            "interactions": ["press:f2", "invalid:target", "click:#button"],
            "explanation": "Unknown action types should provide helpful suggestions"
        },
        {
            "name": "Empty Targets",
            "interactions": ["press:", "click:", "wait:"],
            "explanation": "Missing targets should explain what's needed"
        },
        {
            "name": "Invalid Wait Duration",
            "interactions": ["wait:not_a_number", "wait:-1.0"],
            "explanation": "Non-numeric or negative durations should show examples"
        }
    ]

    for example in mistake_examples:
        print(f"\n📋 Example: {example['name']}")
        print(f"   Context: {example['explanation']}")
        print(f"   Invalid interactions: {example['interactions']}")
        print()

        # Validate and show the helpful error messages
        try:
            validation_result = InteractionValidator.validate_sequence(list(example['interactions']))
            if not validation_result.is_valid:
                error_message = InteractionValidator.format_validation_errors(validation_result)
                print(error_message)
        except Exception as e:
            print(f"   Unexpected error: {e}")

        print("-" * 50)


def demo_valid_interactions():
    """Demonstrate that all existing valid interactions continue to work."""
    print("\n✅ Backward Compatibility Demo")
    print("=" * 50)

    valid_examples = [
        {
            "name": "Key Presses",
            "interactions": ["press:f2", "press:enter", "press:escape", "press:ctrl+c"]
        },
        {
            "name": "Element Clicks",
            "interactions": ["click:#button", "click:.submit", "click:Button"]
        },
        {
            "name": "Hover Actions",
            "interactions": ["hover:#menu", "hover:.dropdown", "hover:Button"]
        },
        {
            "name": "Text Input",
            "interactions": ["type:hello world", "type:username", "type:"]
        },
        {
            "name": "Wait Delays",
            "interactions": ["wait:0.5", "wait:1.0", "wait:2.0"]
        },
        {
            "name": "Complex Sequence",
            "interactions": [
                "click:#demo-button",
                "wait:0.5",
                "press:f2",
                "type:test input",
                "hover:.menu",
                "click:#another-button"
            ]
        }
    ]

    for example in valid_examples:
        print(f"\n📋 {example['name']}: {example['interactions']}")

        try:
            validation_result = InteractionValidator.validate_sequence(list(example['interactions']))
            if validation_result.is_valid:
                print(f"   ✅ All {len(example['interactions'])} interactions are valid")
            else:
                print("   ❌ Unexpected validation failure:")
                error_message = InteractionValidator.format_validation_errors(validation_result)
                print(f"   {error_message}")
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")


async def demo_capture_integration():
    """Demonstrate how validation integrates with actual screenshot captures."""
    print("\n🔗 Capture Integration Demo")
    print("=" * 50)

    # Test with invalid interactions
    print("\n1. Testing capture with INVALID interactions:")
    invalid_interactions = ["f2", "button"]  # Missing colons
    print(f"   Attempting capture with: {invalid_interactions}")

    try:
        await capture_app_screenshot(
            ValidationDemoApp,
            context="invalid_demo",
            interactions=invalid_interactions
        )
        print("   ❌ Expected validation error but capture succeeded!")
    except ValueError as e:
        print("   ✅ Validation caught the error as expected:")
        print(f"   Error details:\n{str(e)}")
    except Exception as e:
        print(f"   ❌ Unexpected error type: {type(e).__name__}: {e}")

    # Test with valid interactions
    print("\n2. Testing capture with VALID interactions:")
    valid_interactions = ["press:f2", "click:#demo-button", "wait:0.5"]
    print(f"   Attempting capture with: {valid_interactions}")

    try:
        result = await capture_app_screenshot(
            ValidationDemoApp,
            context="valid_demo",
            interactions=valid_interactions
        )
        if result.success:
            print("   ✅ Capture succeeded with valid interactions")
            print(f"   Screenshot saved to: {result.screenshot_path}")
        else:
            print(f"   ❌ Capture failed: {result.error_message}")
    except Exception as e:
        print(f"   ❌ Unexpected error: {type(e).__name__}: {e}")


def demo_llm_friendly_structure():
    """Demonstrate the LLM-friendly error message structure."""
    print("\n🤖 LLM-Friendly Error Structure Demo")
    print("=" * 50)

    # Create a validation error to examine the structure
    invalid_interactions = ["f2", "invalid:target", "wait:bad"]
    validation_result = InteractionValidator.validate_sequence(invalid_interactions)

    print("Raw validation result structure:")
    print(f"  is_valid: {validation_result.is_valid}")
    print(f"  errors count: {len(validation_result.errors)}")
    print(f"  suggestions count: {len(validation_result.suggestions)}")

    print("\nDetailed error structure (for LLM consumption):")
    for i, error in enumerate(validation_result.errors):
        print(f"  Error {i + 1}:")
        print(f"    index: {error['index']}")
        print(f"    interaction: '{error['interaction']}'")
        print(f"    message: '{error['message']}'")
        print(f"    suggestions: {error['suggestions']}")
        print(f"    examples: {error['examples']}")

    print(f"\nGeneral suggestions: {validation_result.suggestions}")

    print("\nFormatted error message (user-facing):")
    formatted_error = InteractionValidator.format_validation_errors(validation_result)
    print(formatted_error)


async def main():
    """Run all validation demos."""
    print("🚀 textual-snapshots Interaction Validation Demo")
    print("=" * 60)
    print("This demo shows how the enhanced validation system addresses")
    print("the #1 consumer friction point with immediate, actionable feedback.\n")

    # Demo common mistakes and their helpful error messages
    demo_common_mistakes()

    # Demo backward compatibility
    demo_valid_interactions()

    # Demo LLM-friendly error structure
    demo_llm_friendly_structure()

    # Demo integration with capture operations
    await demo_capture_integration()

    print("\n" + "=" * 60)
    print("✅ Demo complete! Key benefits:")
    print("  • Immediate feedback for interaction format mistakes")
    print("  • LLM-friendly error messages with examples and suggestions")
    print("  • 100% backward compatibility with existing valid interactions")
    print("  • Seamless integration with capture operations")
    print("  • Addresses the #1 consumer friction point identified in analysis")


if __name__ == "__main__":
    asyncio.run(main())
