# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**textual-snapshots** is a professional visual testing library for Textual applications. It provides screenshot capture, comparison, and validation capabilities with an extensible plugin architecture designed for AI integration and enterprise workflows.

Key components:
- **Core Engine**: Screenshot capture with SVG/PNG support via Textual's pilot system
- **CLI Tool**: Rich-formatted command-line interface for batch operations
- **Plugin System**: Extensible hooks for custom workflows and AI integration
- **Validation Suite**: Quality metrics and proactive error detection
- **Comparison Engine**: Visual regression testing capabilities

## Development Commands

### Python-based commands (recommended - cross-platform):
**Uses UV for dependency management and virtual environment handling.**
```bash
# Setup and installation
python dev.py install          # Full development setup with Playwright
python dev.py install-ci       # CI setup without browsers

# Quality checks (run these before commits)
python dev.py check            # Basic: lint + typecheck + test  
python dev.py check --strict   # Strict type checking
python dev.py check --full     # Comprehensive: format + coverage

# Code quality
python dev.py format           # Format code with ruff
python dev.py lint             # Run linting only
python dev.py typecheck        # Type checking with mypy

# Testing
python dev.py test             # Run tests
python dev.py test --coverage  # Run with coverage
python dev.py coverage-html    # Generate and open HTML coverage report

# Utilities  
python dev.py clean            # Clean generated files
python dev.py demo             # Test CLI functionality
python dev.py info             # Show environment info
```

### Make-based commands (alternative):
```bash
make install     # Setup development environment
make check       # Basic quality checks
make check-full  # Comprehensive checks with coverage
make test        # Run tests
make format      # Format code
make clean       # Clean generated files
```

### Testing specific scenarios:
```bash
# Run specific test categories
pytest tests/unit/ -v                    # Unit tests only
pytest tests/ -m "not slow" -v          # Exclude slow tests  
pytest tests/ -m screenshot -v          # Screenshot tests only

# Test single file/function
pytest tests/unit/test_capture_core.py::test_basic_capture -v
```

## Architecture Overview

### Core Package Structure (`src/textual_snapshots/`)

**Primary Modules:**
- `capture.py` - Core screenshot engine with `ScreenshotCapture` class and async capture logic
- `cli.py` - Rich-formatted CLI with discovery, comparison, and conversion commands
- `plugins.py` - Plugin protocol and base classes for extensibility hooks
- `types.py` - Type definitions and protocols (AppContext, ValidationResult, etc.)
- `conversion.py` - Format conversion (SVG ↔ PNG) with quality control
- `validation.py` - Quality metrics and validation suite
- `detection.py` - Proactive error detection for common issues
- `comparison.py` - Visual comparison and diff utilities
- `quality.py` - Quality metrics and assessment tools
- `utils.py` - Common utilities and helper functions

**Key Design Patterns:**
- **Plugin Architecture**: Pre/post capture hooks, success/failure callbacks
- **Context-based Capture**: `AppContext` protocol for flexible app instantiation
- **Async-first**: All capture operations are async using Textual's pilot system
- **Quality-aware**: Built-in metrics tracking and validation
- **Protocol-based**: Uses typing.Protocol for extensible interfaces
- **Budget-free**: Legacy budget system removed for simpler architecture

### Plugin System Architecture

The plugin system uses Protocol-based interfaces for maximum flexibility:

```python
class CapturePlugin(Protocol):
    async def pre_capture(self, context: str, app_context: AppContext) -> dict[str, Any]
    async def post_capture(self, result: CaptureResult, metadata: dict[str, Any]) -> None  
    async def on_success(self, result: CaptureResult) -> None
    async def on_failure(self, error: Exception, context: str) -> None
```

Plugins enable:
- Custom validation logic
- AI integration workflows
- Quality metric collection
- Training data preparation
- Custom output formats

### CLI Architecture

The CLI (`textual-snapshot` command) provides:
- **Auto-discovery**: Finds Textual apps in codebase automatically
- **Interactive selection**: Multiple apps found = interactive picker
- **Batch operations**: Recursive processing with progress indicators
- **Rich output**: Colored output, progress bars, formatted tables
- **Error handling**: Graceful failures with actionable error messages

## Testing Strategy

**Test Structure:**
```
tests/
├── conftest.py           # Fixtures and test utilities
├── framework/            # Framework-specific test utilities
├── unit/                 # Fast unit tests
│   ├── test_capture_core.py    # Core screenshot functionality
│   ├── test_plugins.py         # Plugin system testing  
│   ├── test_validation.py      # Validation suite tests
│   ├── test_conversion.py      # Format conversion tests
│   └── test_detection.py       # Error detection tests
└── integration/          # Slower integration tests
```

**Key Test Fixtures (conftest.py):**
- `PredictableTestApp` - Deterministic Textual app for consistent screenshots
- `InteractiveTestApp` - App with button interactions for workflow testing
- `MockAppContext` - Mock context for testing without real app dependencies  
- `TestPlugin` - Mock plugin for verifying plugin system functionality
- `temp_screenshots_dir` - Isolated temp directory for screenshot output

**Test Categories (markers):**
- `@pytest.mark.slow` - Long-running tests (excluded in quick checks)
- `@pytest.mark.integration` - Integration tests requiring full setup
- `@pytest.mark.screenshot` - Tests that capture actual screenshots

## Configuration Files

**pyproject.toml** contains:
- Dependencies: `textual>=0.41.0`, `playwright>=1.54.0`, `pydantic>=2.0.0`
- Development tools: `pytest`, `mypy`, `ruff`, `coverage`
- Quality settings: Strict mypy config, ruff linting rules
- Test configuration: Async mode, markers, coverage settings

**Key Quality Standards:**
- **Type checking**: Strict mypy with `disallow_untyped_defs = true`
- **Linting**: Ruff with pycodestyle, flake8-bugbear, pyupgrade
- **Code formatting**: Ruff formatter with 100-character line length
- **Test coverage**: Source coverage reporting with HTML output

## Browser Dependencies

For PNG format support:
```bash
pip install playwright
playwright install chromium  # Required for high-quality PNG conversion
```

The library gracefully degrades to SVG-only mode if Playwright/browser unavailable.

## Performance Considerations

- **Caching**: 1-hour TTL for repeated captures (configurable via `CACHE_TTL_SECONDS`)
- **Async operations**: All capture logic is fully async
- **Batch processing**: CLI supports recursive directory processing
- **Memory management**: Textual app instances are properly cleaned up after capture

## Development Workflow

1. **Setup**: `python dev.py install` (installs deps + Playwright browsers)
2. **Development**: Write code, tests run automatically detect issues
3. **Quality check**: `python dev.py check` before commits (lint + typecheck + test)
4. **Comprehensive check**: `python dev.py check --full` for coverage and formatting
5. **CI Integration**: GitHub Actions runs on Python 3.9-3.12 matrix

## Common Tasks

**Adding new plugin hooks:**
1. Extend `CapturePlugin` protocol in `plugins.py`
2. Update `ScreenshotCapture._execute_plugin_hooks()` in `capture.py`
3. Add corresponding test cases in `tests/unit/test_plugins.py`

**Adding CLI commands:**
1. Add Click command in `cli.py` with Rich formatting
2. Update `main()` function to include new command
3. Add integration tests for CLI functionality

**Format conversion features:**
1. Extend conversion logic in `conversion.py`
2. Update quality metrics in `quality.py` if needed
3. Add test cases with sample SVG/PNG files

## Core Classes and Entry Points

**Key Classes:**
- `ScreenshotCapture` - Main capture engine class in `capture.py`
- `BasicAppContext` - Basic AppContext implementation for generic Textual apps
- `CaptureResult` - Result object containing screenshot paths and metadata
- `BasePlugin` - Base plugin implementation in `plugins.py`

**Main Entry Points:**
- `capture_app_screenshot()` function - Simplified screenshot capture
- `textual-snapshot` CLI command - Full CLI interface
- CLI auto-discovery - Automatically finds Textual apps in codebase

**Package Manager:**
- Uses **UV** (`uv`) for fast dependency management and virtual environments
- All commands run through `uv run` for consistency
- Lock file: `uv.lock` for reproducible builds