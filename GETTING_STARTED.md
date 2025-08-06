# Getting Started Guide

Complete guide to get textual-snapshots running, from installation to development setup.

## Installation

Get textual-snapshots running in under 2 minutes.

### Quick Install (Recommended)

```bash
pip install textual-snapshots
```

**Verify installation:**
```bash
textual-snapshot --version
# textual-snapshot, version 0.1.0
```

### Installation Options

#### Basic Installation
```bash
# Core package with SVG support
pip install textual-snapshots
```

#### With PNG Support
```bash
# Install textual-snapshots
pip install textual-snapshots

# Install PNG conversion dependencies
# macOS:
brew install librsvg

# Ubuntu/Debian:
sudo apt-get install librsvg2-bin

# Windows (WSL recommended):
sudo apt-get install librsvg2-bin
```

#### Development Installation
```bash
# Clone repository
git clone https://github.com/testinator-dev/textual-snapshots
cd textual-snapshots

# Install with development dependencies
uv install --dev
# or: pip install -e ".[dev]"

# Verify development setup
pytest tests/
```

### System Requirements

- **Python**: 3.9+ (recommended: 3.11+)
- **Operating System**: macOS, Linux, Windows (with WSL)
- **Dependencies**:
  - `textual>=0.41.0` - TUI framework
  - `pydantic>=2.0.0` - Data validation
  - `click>=8.0.0` - CLI framework
  - `rich>=13.0.0` - Terminal formatting
  - `pillow>=9.0.0` - Image processing

#### Optional Dependencies

- **PNG Support**: `librsvg` (system package)
- **Development**: `pytest`, `mypy`, `ruff`, `coverage`
- **AI Integration**: `pydantic-ai` (future feature)

### Verification

#### Test Basic Installation
```bash
# Check version
textual-snapshot --version

# Test help system
textual-snapshot --help

# Test auto-discovery (should show "No Textual applications found" if none present)
textual-snapshot capture
```

#### Test PNG Support (Optional)
```bash
# Check if rsvg-convert is available
which rsvg-convert

# If available, test conversion
echo '<svg width="100" height="100"><rect width="100" height="100" fill="red"/></svg>' > test.svg
rsvg-convert --format png --output test.png test.svg
ls -la test.png  # Should show PNG file created
rm test.svg test.png  # Cleanup
```

### Common Installation Issues

#### Issue: `textual-snapshot: command not found`

**Cause**: Installation path not in system PATH.

**Solution**:
```bash
# Check if pip installed to user directory
pip show textual-snapshots

# Add to PATH (Linux/macOS)
export PATH="$PATH:$HOME/.local/bin"

# Or install globally
sudo pip install textual-snapshots
```

#### Issue: `ModuleNotFoundError: No module named 'textual'`

**Cause**: Textual not installed or version conflict.

**Solution**:
```bash
# Upgrade textual
pip install --upgrade textual

# Check version
python -c "import textual; print(textual.__version__)"
# Should be 0.41.0 or higher
```

#### Issue: PNG conversion fails with "rsvg-convert not found"

**Cause**: SVG-to-PNG conversion tool not installed.

**Solution**:
```bash
# macOS
brew install librsvg

# Ubuntu/Debian
sudo apt-get update
sudo apt-get install librsvg2-bin

# Arch Linux
sudo pacman -S librsvg

# Windows
# Use WSL and install via apt-get
```

#### Issue: Permission denied errors

**Cause**: Insufficient permissions for screenshot directory.

**Solution**:
```bash
# Create screenshots directory manually
mkdir -p screenshots
chmod 755 screenshots

# Or use custom output directory
textual-snapshot capture --output-dir ~/my-screenshots
```

---

## Your First Screenshot in 5 Minutes

Let's capture your first Textual app screenshot. This tutorial gets you from zero to working visual testing in under 5 minutes.

### Prerequisites

- Python 3.9+ installed
- textual-snapshots installed (`pip install textual-snapshots`)
- A Textual app (we'll create one if you don't have one)

### Step 1: Create a Simple Textual App (2 minutes)

If you already have a Textual app, skip to [Step 2](#step-2-capture-your-first-screenshot).

Create a file named `demo_app.py`:

```python
# demo_app.py
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button, Static

class DemoApp(App):
    """A simple demo application for screenshot testing."""
    
    CSS_PATH = None
    TITLE = "Screenshot Demo App"
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Welcome to textual-snapshots!", id="welcome")
        yield Button("Click Me!", id="demo-button", variant="primary")
        yield Footer()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "demo-button":
            event.button.label = "Clicked!"

if __name__ == "__main__":
    app = DemoApp()
    app.run()
```

**Test your app:**
```bash
python demo_app.py
# Press Ctrl+C to exit
```

You should see a simple TUI with a header, button, and footer.

### Step 2: Capture Your First Screenshot (1 minute)

#### Method 1: Using CLI (Easiest)

```bash
# Auto-discover and capture
textual-snapshot capture

# Or specify the app directly
textual-snapshot capture demo_app.py
```

**Expected output:**
```
✓ Screenshot captured successfully

Path: screenshots/capture_20250805_143021.svg
Size: 15,234 bytes  
Format: svg
Timestamp: 2025-08-05 14:30:21 UTC
```

#### Method 2: Using Python API

Create `test_demo.py`:

```python
# test_demo.py
import asyncio
from textual_snapshots import capture_app_screenshot
from demo_app import DemoApp

async def main():
    result = await capture_app_screenshot(DemoApp(), context="homepage")
    print(f"✓ Screenshot saved: {result.screenshot_path}")
    print(f"✓ File size: {result.file_size_bytes:,} bytes")
    print(f"✓ Success: {result.success}")

if __name__ == "__main__":
    asyncio.run(main())
```

Run it:
```bash
python test_demo.py
```

### Step 3: View Your Screenshot (30 seconds)

#### In Browser (SVG files)
```bash
# Open SVG in default browser
open screenshots/capture_*.svg        # macOS
xdg-open screenshots/capture_*.svg    # Linux
```

#### Convert to PNG (if rsvg-convert installed)
```bash
textual-snapshot convert screenshots/capture_*.svg --to png
open converted/capture_*.png          # macOS
```

#### Terminal Preview (Quick check)
```bash
ls -la screenshots/
# Should show your SVG file with timestamp
```

### Step 4: Advanced Screenshot - User Interactions (1 minute)

Let's capture the app after clicking the button:

#### Using CLI with Interactions
```bash
textual-snapshot capture demo_app.py \
  --context "button_clicked" \
  --interactions "click:#demo-button,wait:0.5"
```

#### Using Python API
```python
# test_interactive.py
import asyncio
from textual_snapshots import capture_app_screenshot
from demo_app import DemoApp

async def main():
    result = await capture_app_screenshot(
        DemoApp(),
        context="button_clicked",
        interactions=[
            "click:#demo-button",  # Click the button
            "wait:0.5"            # Wait for any animations
        ]
    )
    print(f"✓ Interactive screenshot: {result.screenshot_path}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Step 5: Compare Screenshots (30 seconds)

Now you have two screenshots - let's compare them:

```bash
textual-snapshot compare \
  screenshots/capture_*.svg \
  screenshots/button_clicked_*.svg \
  --threshold 0.8
```

**Expected output:**
```
Comparison Results
┌─────────────────────────┬────────────┬────────┬─────────────────────┐
│ File                    │ Similarity │ Status │ Notes               │
├─────────────────────────┼────────────┼────────┼─────────────────────┤
│ capture_20250805.svg    │      0.756 │   ✗    │ Below threshold     │
└─────────────────────────┴────────────┴────────┴─────────────────────┘

✗ 1 of 1 comparisons failed
```

Great! The comparison detected the visual difference (button text changed).

### Congratulations!

🎉 **You've successfully:**
- Created a Textual app
- Captured your first screenshot  
- Captured an interactive screenshot
- Compared screenshots for differences

#### What You've Learned

- **Basic capture**: `textual-snapshot capture app.py`
- **Context naming**: `--context "descriptive_name"`
- **User interactions**: `--interactions "click:#button,wait:0.5"`
- **Comparison**: `textual-snapshot compare baseline.svg current.svg`

#### Your Screenshot Files

Check your project directory:
```
your-project/
├── demo_app.py
├── test_demo.py
└── screenshots/
    ├── capture_20250805_143021.svg     # Initial state
    └── button_clicked_20250805_143045.svg  # After button click
```

---

## Testing Integration

Complete guide for integrating textual-snapshots into your test suite with pytest patterns, fixtures, and organization strategies.

### Quick Integration (2 minutes)

#### 1. Add Screenshot Tests to Existing Suite

```python
# test_visual.py
import pytest
from textual_snapshots import capture_app_screenshot
from my_app import MyApp

@pytest.mark.asyncio
@pytest.mark.screenshot
async def test_homepage_visual():
    result = await capture_app_screenshot(MyApp, context="homepage")
    assert result.success
    assert result.screenshot_path.exists()

@pytest.mark.asyncio
@pytest.mark.screenshot  
async def test_login_visual():
    result = await capture_app_screenshot(
        MyApp,
        context="login_form",
        interactions=["click:#login-tab"]
    )
    assert result.success
```

#### 2. Run Visual Tests

```bash
# Run only screenshot tests
pytest -m screenshot

# Run with verbose output
pytest -m screenshot -v

# Run specific test file
pytest test_visual.py -v
```

#### 3. Configure pytest

Add to `pyproject.toml`:
```toml
[tool.pytest.ini_options]
markers = [
    "screenshot: marks tests as screenshot tests",
    "slow: marks tests as slow running",
]
testpaths = ["tests"]
asyncio_mode = "auto"
```

That's it! You now have visual testing integrated into your test suite.

### Test Organization Patterns

#### 1. Dedicated Visual Test Files

```
tests/
├── unit/
│   ├── test_models.py
│   └── test_utils.py
├── integration/
│   ├── test_workflows.py
│   └── test_api.py
└── visual/
    ├── test_homepage.py
    ├── test_forms.py
    ├── test_responsive.py
    └── conftest.py  # Visual test fixtures
```

#### 2. Mixed Integration

```python
# test_app_features.py - Mix functional and visual tests
import pytest
from textual_snapshots import capture_app_screenshot
from my_app import MyApp

class TestUserRegistration:
    @pytest.mark.asyncio
    async def test_registration_logic(self):
        """Test registration business logic."""
        app = MyApp()
        result = app.register_user("test@example.com", "password")
        assert result.success
    
    @pytest.mark.asyncio
    @pytest.mark.screenshot
    async def test_registration_visual(self):
        """Test registration form appearance."""
        result = await capture_app_screenshot(
            MyApp,
            context="registration_form",
            interactions=["click:#register-tab"]
        )
        assert result.success
    
    @pytest.mark.asyncio
    @pytest.mark.screenshot
    async def test_registration_success_visual(self):
        """Test registration success screen."""
        result = await capture_app_screenshot(
            MyApp,
            context="registration_success",
            interactions=[
                "click:#register-tab",
                "click:#email", "type:test@example.com",
                "click:#password", "type:password123",
                "click:#register-button",
                "wait:1.0"
            ]
        )
        assert result.success
```

#### 3. Page Object Pattern

```python
# page_objects.py
from textual_snapshots import capture_app_screenshot

class HomePage:
    def __init__(self, app_class):
        self.app_class = app_class
    
    async def capture_default(self):
        return await capture_app_screenshot(
            self.app_class,
            context="homepage_default"
        )
    
    async def capture_with_user_menu(self):
        return await capture_app_screenshot(
            self.app_class,
            context="homepage_user_menu",
            interactions=["click:#user-avatar"]
        )

class LoginPage:
    def __init__(self, app_class):
        self.app_class = app_class
    
    async def capture_empty_form(self):
        return await capture_app_screenshot(
            self.app_class,
            context="login_empty",
            interactions=["click:#login-tab"]
        )
    
    async def capture_validation_errors(self):
        return await capture_app_screenshot(
            self.app_class,
            context="login_errors",
            interactions=[
                "click:#login-tab",
                "click:#login-button"  # Trigger validation
            ]
        )

# test_pages.py
import pytest
from page_objects import HomePage, LoginPage
from my_app import MyApp

@pytest.fixture
def home_page():
    return HomePage(MyApp)

@pytest.fixture  
def login_page():
    return LoginPage(MyApp)

@pytest.mark.asyncio
@pytest.mark.screenshot
async def test_homepage_states(home_page):
    """Test different homepage states."""
    
    # Default state
    result = await home_page.capture_default()
    assert result.success
    
    # With user menu
    result = await home_page.capture_with_user_menu()
    assert result.success

@pytest.mark.asyncio
@pytest.mark.screenshot
async def test_login_validation(login_page):
    """Test login form validation states."""
    
    # Empty form
    result = await login_page.capture_empty_form()
    assert result.success
    
    # Validation errors
    result = await login_page.capture_validation_errors()
    assert result.success
```

### Fixtures and Utilities

#### 1. Basic Fixtures

```python
# conftest.py
import pytest
from pathlib import Path
from textual_snapshots import capture_app_screenshot
from my_app import MyApp

@pytest.fixture
def app_class():
    """Provide the main app class for testing."""
    return MyApp

@pytest.fixture
def screenshots_dir():
    """Ensure screenshots directory exists."""
    screenshots_path = Path("screenshots")
    screenshots_path.mkdir(exist_ok=True)
    return screenshots_path

@pytest.fixture
async def basic_screenshot(app_class):
    """Capture basic app screenshot."""
    result = await capture_app_screenshot(app_class, context="basic")
    yield result
    # Cleanup logic here if needed

@pytest.mark.asyncio
async def test_with_basic_fixture(basic_screenshot):
    assert basic_screenshot.success
    assert basic_screenshot.context == "basic"
```

#### 2. Advanced Fixtures

```python
# conftest.py - Advanced fixtures
import pytest
import asyncio
from pathlib import Path
from datetime import datetime
from textual_snapshots import capture_app_screenshot, ScreenshotFormat
from my_app import MyApp

class ScreenshotTestHelper:
    """Helper class for screenshot testing."""
    
    def __init__(self, app_class, base_dir: Path):
        self.app_class = app_class
        self.base_dir = base_dir
        self.captured_screenshots = []
    
    async def capture(self, context: str, interactions=None, format=ScreenshotFormat.SVG):
        """Capture screenshot with tracking."""
        result = await capture_app_screenshot(
            self.app_class,
            context=context,
            interactions=interactions,
            output_format=format,
            output_dir=self.base_dir
        )
        self.captured_screenshots.append(result)
        return result
    
    def cleanup(self):
        """Clean up captured screenshots."""
        for result in self.captured_screenshots:
            if result.screenshot_path.exists():
                result.screenshot_path.unlink()

@pytest.fixture
async def screenshot_helper(app_class, screenshots_dir):
    """Provide screenshot helper with cleanup."""
    helper = ScreenshotTestHelper(app_class, screenshots_dir)
    yield helper
    helper.cleanup()  # Automatic cleanup after test

@pytest.fixture(scope="session")
def baseline_dir():
    """Baseline screenshots directory."""
    baseline_path = Path("baselines")
    baseline_path.mkdir(exist_ok=True)
    return baseline_path

@pytest.fixture
def comparison_helper(screenshots_dir, baseline_dir):
    """Helper for comparing screenshots with baselines."""
    
    class ComparisonHelper:
        def __init__(self, screenshots_dir, baseline_dir):
            self.screenshots_dir = screenshots_dir
            self.baseline_dir = baseline_dir
        
        def compare_with_baseline(self, context: str, tolerance=0.95):
            screenshot_file = next(self.screenshots_dir.glob(f"{context}_*.svg"))
            baseline_file = self.baseline_dir / f"{context}_baseline.svg"
            
            if not baseline_file.exists():
                # Create baseline if it doesn't exist
                import shutil
                shutil.copy2(screenshot_file, baseline_file)
                return True, "Baseline created"
            
            # Use textual-snapshot compare CLI
            import subprocess
            result = subprocess.run([
                "textual-snapshot", "compare",
                str(baseline_file), str(screenshot_file),
                "--threshold", str(tolerance)
            ], capture_output=True, text=True)
            
            return result.returncode == 0, result.stdout
    
    return ComparisonHelper(screenshots_dir, baseline_dir)
```

#### 3. Parameterized Test Fixtures

```python
# Parameterized testing with fixtures
import pytest
from textual_snapshots import capture_app_screenshot

@pytest.fixture(params=[
    ("dark", "desktop"),
    ("dark", "mobile"),
    ("light", "desktop"), 
    ("light", "mobile")
])
def theme_resolution_config(request):
    """Parameterized theme and resolution configurations."""
    theme, resolution = request.param
    return {
        "theme": theme,
        "resolution": resolution,
        "context": f"theme_{theme}_{resolution}"
    }

@pytest.mark.asyncio
@pytest.mark.screenshot
async def test_responsive_themes(app_class, theme_resolution_config):
    """Test all theme/resolution combinations."""
    config = theme_resolution_config
    
    # Configure app
    app = app_class()
    app.theme = config["theme"]
    app.resolution = config["resolution"]
    
    result = await capture_app_screenshot(
        app,
        context=config["context"]
    )
    
    assert result.success
    # Verify screenshot reflects configuration
    assert config["theme"] in result.context
    assert config["resolution"] in result.context

@pytest.fixture(params=[
    {"name": "homepage", "interactions": []},
    {"name": "login", "interactions": ["click:#login-tab"]},
    {"name": "search", "interactions": ["click:#search", "type:test query"]},
])
def page_interaction_config(request):
    """Parameterized page interaction configurations."""
    return request.param

@pytest.mark.asyncio
@pytest.mark.screenshot  
async def test_page_interactions(app_class, page_interaction_config):
    """Test different page interaction scenarios."""
    config = page_interaction_config
    
    result = await capture_app_screenshot(
        app_class,
        context=config["name"],
        interactions=config["interactions"]
    )
    
    assert result.success
    assert config["name"] in result.context
```

### Best Practices Summary

#### 1. Test Organization
- **Separate visual tests** into dedicated files or directories
- **Use descriptive test names** that indicate what's being tested visually
- **Group related tests** into test classes for better organization
- **Use appropriate markers** for test selection and filtering

#### 2. Fixture Design
- **Create reusable fixtures** for common app configurations
- **Use session-scoped fixtures** for expensive setup operations
- **Implement cleanup logic** to manage test data and files
- **Parameterize fixtures** for testing multiple scenarios

#### 3. Performance
- **Run visual tests separately** from unit tests for faster feedback
- **Use parallel execution** for large visual test suites
- **Implement caching** for screenshots and test data
- **Monitor test execution time** and optimize slow tests

#### 4. Maintenance
- **Regular baseline updates** to prevent drift
- **Automated cleanup** of old screenshots and artifacts
- **Environment-specific configuration** for different testing contexts
- **Debug helpers** for development and troubleshooting

---

## Development Setup

### Developer Experience

textual-snapshots provides multiple ways to run development commands, ensuring compatibility across all platforms and developer preferences.

#### Quick Start

Choose your preferred command runner:

```bash
# Option 1: Python script (works everywhere)
python dev.py install
python dev.py check

# Option 2: Make (traditional, widely supported)
make install
make check

# Option 3: Just (modern, fast)
just install
just check
```

#### Command Runners

##### Python Script (`dev.py`) - **Recommended**

The Python-based developer script provides full cross-platform compatibility:

```bash
# Setup
python dev.py install          # Full development setup
python dev.py install-ci       # CI environment (no browser)

# Code Quality  
python dev.py format           # Format code
python dev.py format --check   # Check formatting only
python dev.py lint             # Run linting
python dev.py typecheck        # Type checking
python dev.py typecheck --strict  # Strict type checking

# Testing
python dev.py test             # Run tests
python dev.py test --quiet     # Quiet test output
python dev.py test --coverage  # With coverage report

# Quality Checks (combinations)
python dev.py check            # Basic checks (lint + typecheck + test)
python dev.py check --strict   # Strict checks
python dev.py check --full     # Comprehensive (format + lint + typecheck + coverage)

# CLI Testing
python dev.py cli-test         # Test CLI commands
python dev.py demo             # Run CLI demo

# Reports
python dev.py coverage-html    # Generate and open HTML coverage
python dev.py coverage-xml     # Generate XML coverage (CI)

# Utilities
python dev.py clean            # Clean generated files
python dev.py reset            # Reset environment (clean + reinstall)
python dev.py deps-update      # Update dependencies
python dev.py info             # Show environment info

# Git Workflow
python dev.py pre-commit       # Run before committing (strict checks)
python dev.py pre-push         # Run before pushing (full checks)
```

**Advantages:**
- ✅ **Universal compatibility** (Windows, macOS, Linux)
- ✅ **No external dependencies** (just Python)
- ✅ **Rich output** with colors and status indicators
- ✅ **Detailed error handling** and progress feedback
- ✅ **Verbose mode** for debugging (`-v` flag)

#### Development Workflow

##### Initial Setup

1. **Clone repository:**
   ```bash
   git clone <repository-url>
   cd textual-snapshots
   ```

2. **Setup development environment:**
   ```bash
   # Choose one method:
   python dev.py install    # Python script (recommended)
   make install            # Make
   just install            # Just
   ```

3. **Verify setup:**
   ```bash
   python dev.py info      # Check environment status
   python dev.py demo      # Test CLI functionality
   ```

##### Daily Development

1. **Make changes** to code

2. **Run quality checks:**
   ```bash
   python dev.py check     # Basic checks
   python dev.py check --strict  # Before committing
   ```

3. **Test specific features:**
   ```bash
   python dev.py test --coverage  # Full test suite
   pytest tests/unit/test_specific.py  # Specific tests
   ```

4. **Pre-commit validation:**
   ```bash
   python dev.py pre-commit  # Comprehensive checks
   ```

#### Code Quality Standards

##### Formatting
- **Tool:** `ruff format`
- **Style:** Black-compatible formatting
- **Line Length:** 88 characters (Black default)
- **Import Sorting:** Automatic with ruff

##### Linting
- **Tool:** `ruff check`
- **Rules:** Comprehensive rule set including:
  - `E`, `W` - pycodestyle errors and warnings
  - `F` - Pyflakes
  - `UP` - pyupgrade (modern Python syntax)
  - `B` - flake8-bugbear
  - `C4` - flake8-comprehensions
  - `I` - isort compatibility

##### Type Checking
- **Tool:** `mypy`
- **Mode:** Strict for source code
- **Test Mode:** Relaxed for test files (built-in relaxed settings)
- **Coverage:** 100% type annotation coverage required

##### Testing
- **Framework:** pytest
- **Coverage Target:** >90%
- **Marker Support:** 
  - `@pytest.mark.asyncio` for async tests
  - `@pytest.mark.integration` for integration tests
  - `@pytest.mark.slow` for slow tests

#### Troubleshooting

**Common Issues:**

1. **`uv` not found:**
   ```bash
   # Install UV package manager
   curl -LsSf https://astral.sh/uv/install.sh | sh  # Unix
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows
   ```

2. **Playwright/Chromium issues:**
   ```bash
   uv run playwright install chromium --with-deps
   ```

3. **Permission errors:**
   ```bash
   chmod +x dev.py           # Make Python script executable
   ```

4. **Virtual environment issues:**
   ```bash
   python dev.py reset       # Reset entire environment
   ```

**Getting Help:**

- Run `python dev.py --help` for command help
- Run `make help` for Makefile targets  
- Run `just --list` for Just commands
- Check GitHub Issues for known problems

---

## Next Steps

Now that you have textual-snapshots set up and working:

1. **Explore advanced features** - Try plugins, batch processing, and CI/CD integration
2. **Read the API Reference** - Learn about all available functions and options
3. **Join the community** - Get help and share your experiences
4. **Contribute** - Help improve textual-snapshots for everyone

### Troubleshooting

Still having issues? Check these resources:

#### Screenshot is blank or corrupted
- Ensure your app runs correctly: `python demo_app.py`
- Check app initialization doesn't require user input
- Try increasing wait time: `--interactions "wait:1.0"`

#### Permission denied errors
```bash
mkdir -p screenshots
chmod 755 screenshots
```

#### Command not found
```bash
pip install --upgrade textual-snapshots
which textual-snapshot  # Should show installation path
```

Need help? Open an issue on [GitHub](https://github.com/testinator-dev/textual-snapshots/issues) or join our [community discussions](https://github.com/testinator-dev/textual-snapshots/discussions).

---

**You're now ready for production visual testing!** 📸 Your test suite has comprehensive screenshot capabilities that will grow with your application.