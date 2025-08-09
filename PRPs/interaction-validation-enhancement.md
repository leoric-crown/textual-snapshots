name: "Interaction Format Validation Enhancement"
description: |

## Purpose
Implement comprehensive interaction validation with LLM-friendly error messages to address the #1 consumer friction point in textual-snapshots. This PRP builds on our research findings and consumer analysis to enhance the interaction parameter validation system with immediate, actionable feedback.

## Core Principles
1. **Context is King**: Include ALL necessary documentation, examples, and caveats
2. **Validation Loops**: Provide executable tests/lints the AI can run and fix
3. **Information Dense**: Use keywords and patterns from the codebase
4. **Progressive Success**: Start simple, validate, then enhance
5. **Global rules**: Be sure to follow all rules in CLAUDE.md

---

## Goal
Transform textual-snapshots interaction validation from silent failures to immediate, LLM-friendly error messages that guide users to correct usage patterns. Address the critical consumer experience issue where incorrect interaction formats fail silently, causing confusion and development friction.

## Why
- **Business value**: Eliminate #1 consumer friction point identified in CONSUMER_ANALYSIS.md
- **User impact**: Provide immediate, actionable feedback for interaction format mistakes
- **Integration**: Leverage existing Pydantic validation patterns in textual-snapshots
- **LLM Support**: Enable AI assistants to self-correct interaction format mistakes

## What
Enhance the `_perform_interactions` method in `capture.py` with upfront Pydantic validation that provides comprehensive, LLM-friendly error messages with examples and fix suggestions.

### Success Criteria
- [ ] All interaction format mistakes provide immediate, actionable error messages
- [ ] Error messages include correct format examples and fix suggestions
- [ ] Validation is performed before any Textual pilot operations
- [ ] LLM-consumable structured error information with JSON schema support
- [ ] Backward compatibility with existing interaction patterns
- [ ] Comprehensive test coverage with error scenario validation

## All Needed Context

### Research Context Bundle
**Generated**: 2025-01-XX XX:XX:XX UTC
**Session**: interaction_validation_research

#### Official Documentation Research
**Source**: https://docs.pydantic.dev/latest/concepts/validators/
**Key Patterns**: `@field_validator` with custom error messages, `PydanticCustomError` for structured errors
**Code Examples**: 
```python
@field_validator('field_name', mode='before')
@classmethod
def validate_field(cls, value):
    if not valid_condition:
        raise PydanticCustomError(
            'custom_error_type',
            'Error message with {context}',
            {'context': value}
        )
    return value
```

#### Current Implementation Analysis
**Source**: /Users/Ricardo_Leon1/TestIO/textual-snapshots/src/textual_snapshots/capture.py:518-542
**Current Pattern**: Basic string parsing with silent warnings for unknown commands
**Issue**: `logger.warning(f"Unknown interaction command: {interaction}")` - silent failure

#### Consumer Experience Research
**Source**: CONSUMER_ANALYSIS.md findings
**Critical Issue**: Interaction format confusion is #1 consumer friction point
**Pattern**: Users expect `["f2", "button"]` but need `["press:f2", "click:#button"]`

### Documentation & References
```yaml
- file: /Users/Ricardo_Leon1/TestIO/textual-snapshots/src/textual_snapshots/capture.py
  why: Contains current _perform_interactions method to enhance (lines 518-542)
  critical: Must preserve all existing interaction types and add validation layer

- file: /Users/Ricardo_Leon1/TestIO/textual-snapshots/pyproject.toml
  why: Confirms pydantic>=2.0.0 dependency already available for validation
  critical: No additional dependencies needed

- file: /Users/Ricardo_Leon1/TestIO/textual-snapshots/examples/basic_capture.py
  why: Shows proper interaction format examples to reference in error messages
  critical: Lines 102-105 show correct "click:#demo-button", "wait:0.5" patterns

- file: /Users/Ricardo_Leon1/TestIO/textual-snapshots/src/textual_snapshots/types.py
  why: Contains existing Pydantic patterns and type definitions
  critical: Leverage existing ValidationResult pattern for consistency

- url: https://docs.pydantic.dev/latest/concepts/validators/
  section: Custom error messages and PydanticCustomError
  critical: Use PydanticCustomError for structured, LLM-friendly error messages
```

### Current Codebase Structure
```bash
textual-snapshots/
├── src/textual_snapshots/
│   ├── capture.py          # TARGET: enhance _perform_interactions (lines 518-542)
│   ├── types.py           # Contains existing Pydantic patterns
│   └── __init__.py        # Public API exports
├── examples/
│   └── basic_capture.py   # Shows correct interaction patterns
├── tests/unit/
│   └── test_capture_core.py # Existing test patterns to extend
└── pyproject.toml         # pydantic>=2.0.0 already available
```

### Desired Implementation Structure
```bash
textual-snapshots/
├── src/textual_snapshots/
│   ├── capture.py          # ENHANCED: Add InteractionValidator class + validation
│   ├── interactions.py     # NEW: Pydantic interaction models and validation logic  
│   ├── types.py           # ENHANCED: Add interaction validation result types
│   └── __init__.py        # ENHANCED: Export new validation classes
├── tests/unit/
│   └── test_interactions.py # NEW: Comprehensive interaction validation tests
└── examples/
    └── validation_demo.py  # NEW: Demonstrates error handling and validation
```

### Known Gotchas of our codebase & Library Quirks
```python
# CRITICAL: textual-snapshots already uses pydantic>=2.0.0
# CRITICAL: Must preserve existing interaction types: press:, click:, hover:, type:, wait:
# CRITICAL: Current _perform_interactions method processes interactions sequentially
# CRITICAL: Logger warnings are silent failures - users miss format mistakes

# Library patterns in textual-snapshots:
# - Uses BaseModel from pydantic for CaptureResult (capture.py:115)
# - Uses Field for structured metadata (capture.py:125-161)
# - Follows async/await patterns throughout (capture.py:518)
# - Uses logger for warnings but they're easily missed

# Consumer friction patterns from CONSUMER_ANALYSIS.md:
# ❌ WRONG - Silent failure (most common mistake)
# interactions=["f2", "button", "enter"]
# 
# ✅ CORRECT - Required format  
# interactions=["press:f2", "click:#button", "press:enter"]
```

## Implementation Blueprint

### Enhanced Data Models for Validation

Create comprehensive Pydantic models for interaction validation with LLM-friendly error messages:

```python
# src/textual_snapshots/interactions.py

from pydantic import BaseModel, field_validator
from pydantic_core import PydanticCustomError
from typing import Literal, Union, List
from abc import ABC, abstractmethod

class InteractionValidationError(Exception):
    """Custom exception for interaction validation errors with LLM-friendly context."""
    
    def __init__(self, message: str, suggestions: List[str], examples: List[str]):
        self.message = message
        self.suggestions = suggestions
        self.examples = examples
        super().__init__(message)

class BaseInteraction(BaseModel, ABC):
    """Base class for all interaction types with validation."""
    
    @abstractmethod
    def to_command(self) -> str:
        """Convert to command string format."""
        pass
    
    @classmethod
    @abstractmethod 
    def get_examples(cls) -> List[str]:
        """Get example usage for error messages."""
        pass

class PressInteraction(BaseInteraction):
    type: Literal["press"] = "press"
    key: str
    
    def to_command(self) -> str:
        return f"press:{self.key}"
    
    @classmethod
    def get_examples(cls) -> List[str]:
        return ["press:f2", "press:enter", "press:escape", "press:ctrl+c"]

class ClickInteraction(BaseInteraction):
    type: Literal["click"] = "click"  
    selector: str
    
    def to_command(self) -> str:
        return f"click:{self.selector}"
    
    @classmethod
    def get_examples(cls) -> List[str]:
        return ["click:#button", "click:.submit", "click:Button"]

class ValidationResult(BaseModel):
    """Result of interaction validation with LLM-friendly context."""
    is_valid: bool
    validated_interactions: List[BaseInteraction] = []
    errors: List[InteractionValidationError] = []
    suggestions: List[str] = []
```

### Core Validation Engine

Implement comprehensive validation logic with structured error messages:

```python
# Enhanced _perform_interactions in capture.py

class InteractionValidator:
    """Validates and parses interaction sequences with LLM-friendly errors."""
    
    @classmethod
    def parse_interaction(cls, interaction_string: str) -> BaseInteraction:
        """Parse single interaction with comprehensive error handling."""
        if not isinstance(interaction_string, str):
            raise InteractionValidationError(
                f"Interaction must be string, got {type(interaction_string).__name__}",
                ["Convert to string format", "Use proper interaction syntax"],
                ["press:f2", "click:#button", "wait:1.0"]
            )
            
        if ":" not in interaction_string:
            # CRITICAL: This is the #1 user mistake - provide detailed guidance
            raise InteractionValidationError(
                f"Interaction '{interaction_string}' missing required ':' separator. "
                f"All interactions must use 'type:target' format.",
                [
                    f"Change '{interaction_string}' to 'press:{interaction_string}' for key presses",
                    f"Change '{interaction_string}' to 'click:{interaction_string}' for element clicks",
                    "Use 'type:text' for text input",
                    "Use 'wait:seconds' for delays"
                ],
                [
                    f"press:{interaction_string}  # if this is a key press",
                    f"click:#{interaction_string}  # if this is an element ID",
                    f"click:{interaction_string}  # if this is a CSS selector"
                ]
            )
            
        action_type, target = interaction_string.split(":", 1)
        
        # Validate based on interaction type with specific guidance
        if action_type == "press":
            return PressInteraction(key=target)
        elif action_type == "click":
            return ClickInteraction(selector=target)
        elif action_type == "hover":
            return HoverInteraction(selector=target) 
        elif action_type == "type":
            return TypeInteraction(text=target)
        elif action_type == "wait":
            try:
                duration = float(target)
                return WaitInteraction(duration=duration)
            except ValueError:
                raise InteractionValidationError(
                    f"Wait duration '{target}' must be a number",
                    ["Use decimal numbers for wait times", "Common values: 0.1, 0.5, 1.0, 2.0"],
                    ["wait:0.5", "wait:1.0", "wait:2.0"]
                )
        else:
            raise InteractionValidationError(
                f"Unknown interaction type '{action_type}'",
                [
                    "Use 'press:' for keyboard interactions",
                    "Use 'click:' for mouse clicks", 
                    "Use 'hover:' for hover actions",
                    "Use 'type:' for text input",
                    "Use 'wait:' for delays"
                ],
                [
                    "press:enter",
                    "click:#button", 
                    "hover:.menu-item",
                    "type:hello world",
                    "wait:1.0"
                ]
            )
    
    @classmethod
    def validate_sequence(cls, interactions: List[str]) -> ValidationResult:
        """Validate entire interaction sequence with comprehensive feedback."""
        validated = []
        errors = []
        suggestions = []
        
        for i, interaction in enumerate(interactions):
            try:
                validated_interaction = cls.parse_interaction(interaction)
                validated.append(validated_interaction)
            except InteractionValidationError as e:
                errors.append(e)
                
        # Provide sequence-level suggestions
        if errors:
            suggestions.extend([
                "Check the interaction format documentation for examples",
                "All interactions must use 'type:target' format with colon separator",
                "Common mistake: using bare strings instead of prefixed format"
            ])
            
        return ValidationResult(
            is_valid=len(errors) == 0,
            validated_interactions=validated,
            errors=errors,
            suggestions=suggestions
        )
```

### List of Implementation Tasks

```yaml
Task 1: Create interaction validation models
MODIFY src/textual_snapshots/capture.py:
  - IMPORT InteractionValidator, ValidationResult
  - PRESERVE existing _perform_interactions method structure
  - INJECT validation before pilot operations

CREATE src/textual_snapshots/interactions.py:
  - IMPLEMENT BaseInteraction abstract class
  - IMPLEMENT specific interaction classes (Press, Click, Hover, Type, Wait)
  - IMPLEMENT InteractionValidator with comprehensive error handling
  - INCLUDE LLM-friendly error messages with examples and suggestions

Task 2: Enhance capture.py with validation integration  
MODIFY src/textual_snapshots/capture.py:
  - FIND method: async def _perform_interactions
  - INJECT validation before pilot operations:
    ```python
    # Validate interactions upfront with comprehensive feedback
    validation_result = InteractionValidator.validate_sequence(interactions)
    if not validation_result.is_valid:
        # Create comprehensive error message for users
        error_details = []
        for error in validation_result.errors:
            error_details.append(f"❌ {error.message}")
            error_details.extend([f"💡 {suggestion}" for suggestion in error.suggestions])
            error_details.extend([f"✅ Example: {example}" for example in error.examples])
        
        combined_error = "\n".join(error_details)
        logger.error(f"Interaction validation failed:\n{combined_error}")
        raise ValueError(f"Invalid interaction format. Details:\n{combined_error}")
    ```
  - PRESERVE all existing interaction processing logic
  - MAINTAIN backward compatibility with valid interactions

Task 3: Update type exports and public API
MODIFY src/textual_snapshots/types.py:
  - ADD InteractionValidationResult type
  - ADD interaction error types for external use

MODIFY src/textual_snapshots/__init__.py:
  - ADD exports: InteractionValidator, ValidationResult
  - PRESERVE all existing exports

Task 4: Comprehensive test coverage
CREATE tests/unit/test_interactions.py:
  - TEST each interaction type validation
  - TEST common user mistakes with expected error messages
  - TEST LLM-friendly error message structure
  - TEST backward compatibility with valid interactions
  - INCLUDE performance regression tests

CREATE examples/validation_demo.py:
  - DEMONSTRATE proper error handling patterns
  - SHOW LLM-consumable error message format
  - INCLUDE recovery patterns for common mistakes
```

### Per-task Pseudocode

```python
# Task 1: Core validation logic
class InteractionValidator:
    @classmethod
    def parse_interaction(cls, interaction: str) -> BaseInteraction:
        # PATTERN: Immediate validation with structured feedback
        if ":" not in interaction:
            # CRITICAL: Most common user mistake - provide comprehensive guidance
            raise InteractionValidationError(
                message=f"Missing ':' separator in '{interaction}'",
                suggestions=[
                    f"For key press: 'press:{interaction}'",
                    f"For element click: 'click:{interaction}'", 
                    "Check documentation for format examples"
                ],
                examples=[
                    "press:enter", "click:#button", "wait:1.0"
                ]
            )
        
        action, target = interaction.split(":", 1) 
        # PATTERN: Type-specific validation with examples
        return cls._create_typed_interaction(action, target)

# Task 2: Integration with existing capture system
async def _perform_interactions(self, pilot: Pilot[Any], interactions: list[str]) -> None:
    # PATTERN: Validate first, then execute
    validation_result = InteractionValidator.validate_sequence(interactions)
    
    if not validation_result.is_valid:
        # CRITICAL: Provide immediate, actionable feedback
        error_message = format_validation_errors(validation_result.errors)
        raise ValueError(error_message)
    
    # PATTERN: Use validated interactions (maintains existing logic)
    for validated_interaction in validation_result.validated_interactions:
        await self._execute_validated_interaction(pilot, validated_interaction)
```

### Integration Points
```yaml
VALIDATION:
  - integrate with: src/textual_snapshots/capture.py:_perform_interactions
  - pattern: "Validate before execute, preserve existing logic"
  - error handling: "Structured exceptions with LLM-friendly messages"

TYPE SYSTEM:
  - add to: src/textual_snapshots/types.py
  - pattern: "ValidationResult, InteractionValidationError types"

PUBLIC API:
  - add to: src/textual_snapshots/__init__.py  
  - pattern: "__all__.extend(['InteractionValidator', 'ValidationResult'])"

EXAMPLES:
  - create: examples/validation_demo.py
  - pattern: "Show error handling and recovery patterns"
```

## Multi-Agent Implementation Blueprint

### Agent Delegation Strategy
- **Primary Agent**: `developer` (research-first implementation with MCP tools)
- **Secondary Agents**: `tester` (comprehensive validation test coverage)
- **Required Agents**: `developer` + `tester` (validation logic + comprehensive testing)

### Checkpoint-Based Implementation Plan
1. **Analysis Phase**: Review current interaction parsing and identify validation injection points
2. **Architecture Phase**: Design Pydantic validation models and error message structure  
3. **Implementation Phase**: Create validation classes and integrate with capture.py
4. **Validation Phase**: Comprehensive testing of error scenarios and LLM-friendly messages
5. **Integration Phase**: Update public API and create validation examples

### Implementation Requirements
- Start with Pydantic models showing comprehensive validation approach
- Reference existing capture.py interaction processing patterns
- Include structured error handling with LLM-consumable format
- Specify user feedback requirements with examples and suggestions
- List tasks in checkpoint order with validation gates
- Include mandatory quality gates for error message effectiveness

## Validation Loop

### Level 1: Syntax & Style
```bash
# Run these FIRST - fix any errors before proceeding
ruff check src/textual_snapshots/ --fix  # Auto-fix what's possible
mypy src/textual_snapshots/             # Type checking

# Expected: No errors. If errors, READ the error and fix.
```

### Level 2: Unit Tests for validation logic
```python
# CREATE tests/unit/test_interactions.py with comprehensive error scenario tests:
def test_missing_colon_separator():
    """Test the #1 user mistake - missing colon separator"""
    with pytest.raises(InteractionValidationError) as exc_info:
        InteractionValidator.parse_interaction("f2")
    
    error = exc_info.value
    assert "missing required ':' separator" in error.message.lower()
    assert "press:f2" in error.examples
    assert len(error.suggestions) >= 2

def test_llm_friendly_error_structure():
    """Test error messages are structured for LLM consumption"""
    validation = InteractionValidator.validate_sequence(["invalid", "press:f2"])
    assert not validation.is_valid
    assert len(validation.errors) == 1
    assert validation.errors[0].suggestions
    assert validation.errors[0].examples

def test_backward_compatibility():
    """Test all existing valid interactions still work"""
    valid_interactions = [
        "press:f2", "click:#button", "hover:.menu", "type:text", "wait:1.0"
    ]
    validation = InteractionValidator.validate_sequence(valid_interactions)
    assert validation.is_valid
    assert len(validation.validated_interactions) == 5
```

```bash
# Run and iterate until passing:
uv run pytest tests/unit/test_interactions.py -v
# If failing: Read error, understand root cause, fix validation logic, re-run
```

### Level 3: Integration Test with actual capture
```python
# Test integration with capture_app_screenshot function:
async def test_validation_integration():
    """Test validation errors surface in capture operations"""
    from textual_snapshots import capture_app_screenshot
    
    with pytest.raises(ValueError) as exc_info:
        await capture_app_screenshot(
            TestApp,
            context="error_test",
            interactions=["f2", "button"]  # Invalid format
        )
    
    error_message = str(exc_info.value)
    assert "missing required ':' separator" in error_message.lower()
    assert "press:f2" in error_message
    assert "click:#button" in error_message
```

## Multi-Agent Quality Assurance Framework

### Universal Requirements  
- **Pydantic Integration**: Leverage existing pydantic>=2.0.0 dependency in textual-snapshots
- **Error Message Quality**: All errors provide examples and fix suggestions
- **Backward Compatibility**: All existing valid interactions continue to work unchanged
- **LLM Consumable**: Error structure enables AI self-correction
- **Performance**: Validation adds minimal overhead to interaction processing

### Agent-Specific Focus Areas
- **Code Quality**: Research-driven validation patterns, comprehensive error handling (developer)
- **Testing**: Error scenario coverage, LLM-friendly message validation, integration tests (tester)
- **Message Effectiveness**: Error messages must include examples and actionable suggestions (developer)
- **Consumer Experience**: Address the #1 friction point with immediate, clear feedback (developer)

## Final validation Checklist
- [ ] All common interaction format mistakes provide immediate error messages
- [ ] Error messages include correct format examples: `["press:f2", "click:#button"]`
- [ ] LLM-friendly error structure enables AI self-correction
- [ ] Backward compatibility: all existing valid interactions work unchanged
- [ ] All tests pass: `uv run pytest tests/unit/test_interactions.py -v`
- [ ] No linting errors: `uv run ruff check src/textual_snapshots/`
- [ ] No type errors: `uv run mypy src/textual_snapshots/`
- [ ] Integration test successful with capture_app_screenshot
- [ ] Error messages are informative with actionable suggestions
- [ ] Documentation includes validation examples

---

## Anti-Patterns to Avoid
- ❌ Don't break existing valid interaction patterns - maintain backward compatibility
- ❌ Don't create generic error messages - be specific about the mistake and fix
- ❌ Don't ignore the colon separator issue - it's the #1 user friction point  
- ❌ Don't use silent warnings - users miss them and stay confused
- ❌ Don't validate during execution - validate upfront before pilot operations
- ❌ Don't create complex validation - keep it simple and focused on format mistakes

## Success Metrics
- **Error Coverage**: 100% of common interaction format mistakes provide structured errors
- **Message Quality**: All error messages include examples and fix suggestions  
- **Consumer Experience**: Eliminate silent failures and interaction format confusion
- **LLM Integration**: AI assistants can consume error messages and self-correct
- **Performance**: Validation overhead < 1ms per interaction sequence