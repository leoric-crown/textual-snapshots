# textual-snapshots

**Professional visual testing for Textual applications - start simple, scale with confidence**

[![PyPI version](https://badge.fury.io/py/textual-snapshots.svg)](https://badge.fury.io/py/textual-snapshots)
[![Python versions](https://img.shields.io/pypi/pyversions/textual-snapshots.svg)](https://pypi.org/project/textual-snapshots/)
[![Documentation](https://img.shields.io/badge/docs-available-blue.svg)](docs/)
[![Tests](https://github.com/testinator-dev/textual-snapshots/workflows/Tests/badge.svg)](https://github.com/testinator-dev/textual-snapshots/actions)

## Why textual-snapshots?

**Drop-in replacement for pytest-textual-snapshot with professional features:**

- ✅ **5-minute setup** - From install to working screenshot
- ✅ **Rich interaction capture** - Clicks, keys, complex user workflows  
- ✅ **Professional CLI tools** - Auto-discovery, batch processing, migration
- ✅ **Plugin architecture** - Extensible for custom validation and workflows
- ✅ **CI/CD ready** - GitHub Actions, comparison reports, regression detection
- ✅ **Migration tools** - Seamless transition from pytest-textual-snapshot

## Quick Start (5 minutes)

### 1. Install

```bash
pip install textual-snapshots

# For PNG conversion support (optional)
brew install librsvg  # macOS
# or apt-get install librsvg2-bin  # Linux
```

### 2. First Screenshot

```python
# test_my_app.py
from textual_snapshots import capture_app_screenshot
from my_textual_app import MyApp

async def test_homepage_screenshot():
    result = await capture_app_screenshot(MyApp(), context="homepage")
    assert result.success
    print(f"Screenshot: {result.screenshot_path}")
```

### 3. Run Test

```bash
python -m pytest test_my_app.py -v
# ✓ Screenshot saved to screenshots/homepage_20250805_143021.svg
```

**That's it!** You now have visual testing for your Textual app.

## Common Usage Patterns

### Interactive Screenshots

Capture user workflows with interaction sequences:

```python
from textual_snapshots import capture_app_screenshot

async def test_login_workflow():
    result = await capture_app_screenshot(
        MyApp(),
        context="login_flow",
        interactions=[
            "click:#username",
            "type:testuser@example.com", 
            "press:tab",
            "type:password123",
            "click:#login-btn",
            "wait:1.0"  # Wait for login animation
        ]
    )
    assert result.success
```

### CLI Auto-Discovery

Let textual-snapshots find and capture your apps automatically:

```bash
# Auto-discover Textual apps in current directory
textual-snapshot capture

# Interactive app selection when multiple found
textual-snapshot capture --interactive

# Capture with interactions
textual-snapshot capture --interactions "click:#button,wait:0.5,press:enter"
```

### Comparison and Regression Testing

```bash
# Compare screenshots for visual regressions
textual-snapshot compare baseline.svg current.svg

# Batch comparison with detailed report
textual-snapshot compare baselines/ current/ --recursive --output-report report.json
```

## Plugin System

Extend textual-snapshots with custom validation and workflows:

```python
from textual_snapshots import ScreenshotCapture
from textual_snapshots.plugins import CapturePlugin

class CustomValidationPlugin(CapturePlugin):
    async def post_capture(self, result, metadata):
        # Custom validation logic
        if result.file_size_bytes > 1024 * 1024:  # 1MB
            print(f"Warning: Large screenshot ({result.file_size_bytes:,} bytes)")

capture = ScreenshotCapture(plugins=[CustomValidationPlugin()])
result = await capture.capture_app_screenshot(MyApp(), context="test")
```

## CI/CD Integration

### GitHub Actions - Quick Setup

```yaml
name: Visual Tests
on: [push, pull_request]

jobs:
  visual-tests:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install textual-snapshots pytest-asyncio
        sudo apt-get install librsvg2-bin  # For PNG support
    
    - name: Run visual tests
      run: |
        pytest tests/ -m screenshot
        
    - name: Compare with baselines
      run: |
        textual-snapshot compare baselines/ screenshots/ --fail-on-diff
```

### Advanced CI/CD Features

```yaml
# Advanced workflow with matrix testing and reporting
strategy:
  matrix:
    python-version: ['3.9', '3.10', '3.11', '3.12']
    test-suite: ['core', 'integration', 'e2e']

steps:
- name: Run visual tests with reporting
  run: |
    pytest tests/${{ matrix.test-suite }}/ -m screenshot -v
    textual-snapshot compare baselines/ screenshots/ --output-report visual-report.json

- name: Upload screenshots on failure
  uses: actions/upload-artifact@v4
  if: failure()
  with:
    name: failed-screenshots-${{ matrix.python-version }}-${{ matrix.test-suite }}
    path: |
      screenshots/
      visual-report.json
    retention-days: 30
```

### Multiple Platform Support

```yaml
strategy:
  matrix:
    os: [ubuntu-latest, macos-latest, windows-latest]

steps:
- name: Install dependencies (Ubuntu)
  if: runner.os == 'Linux'
  run: sudo apt-get install -y librsvg2-bin

- name: Install dependencies (macOS)
  if: runner.os == 'macOS'  
  run: brew install librsvg
```

## Development & Contributing

textual-snapshots provides multiple ways to run development commands for excellent cross-platform compatibility.

### Quick Start - Development Setup

```bash
git clone https://github.com/testinator-dev/textual-snapshots
cd textual-snapshots

# Choose your preferred command runner:

# Option 1: Python script (works everywhere) - RECOMMENDED
python dev.py install        # Full setup with Playwright
python dev.py check          # Run all quality checks

# Option 2: Make (traditional)
make install
make check
```

### Key Development Commands

```bash
# Quality Checks
python dev.py check                    # Basic: lint + typecheck + test
python dev.py check --strict           # Strict: includes strict type checking  
python dev.py check --full             # Full: format + lint + typecheck + coverage

# Testing & Coverage
python dev.py test --coverage          # Run tests with coverage
python dev.py coverage-html            # Generate and open HTML coverage

# Code Quality
python dev.py format                   # Format code
python dev.py lint                     # Linting only
python dev.py typecheck --strict       # Type checking

# Utilities  
python dev.py clean                    # Clean generated files
python dev.py info                     # Show environment info
python dev.py demo                     # Test CLI functionality
```

## Examples

Explore real-world usage patterns:

```bash
git clone https://github.com/testinator-dev/textual-snapshots
cd textual-snapshots/examples/

# Basic screenshot examples
python basic_capture.py

# Advanced interaction examples  
python interaction_workflows.py

# Plugin system examples
python custom_plugins.py
```

## Complete Documentation

- 📚 **[Getting Started Guide](GETTING_STARTED.md)** - Detailed installation, first steps, and development setup
- 🔧 **[API Reference](API_REFERENCE.md)** - Complete Python API and CLI documentation  
- 🔒 **[Security Guidelines](SECURITY.md)** - Data privacy and screenshot security best practices

## Community & Support

- 💬 **[GitHub Discussions](https://github.com/testinator-dev/textual-snapshots/discussions)** - Questions and community
- 🐛 **[Issues](https://github.com/testinator-dev/textual-snapshots/issues)** - Bug reports and feature requests  
- 💡 **[Textual Discord](https://discord.gg/Enf6Z3qhVr)** - Join the #testing channel
- 📧 **Email**: team@testinator.dev

---

**Built with ❤️ for the [Textual](https://textual.textualize.io/) community**

*Professional visual testing that grows with your application - from simple screenshots to enterprise CI/CD workflows.*
