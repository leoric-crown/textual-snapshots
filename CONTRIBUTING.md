# Contributing to textual-snapshots

Thank you for considering contributing to textual-snapshots! We welcome contributions from everyone.

## Quick Start

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/textual-snapshots
   cd textual-snapshots
   ```

2. **Set up development environment**
   ```bash
   python dev.py install  # Install dependencies and setup
   python dev.py info     # Verify setup
   ```

3. **Run quality checks**
   ```bash
   python dev.py check    # Lint, type check, and test
   ```

## Development Workflow

### Making Changes

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Follow the existing code style
   - Add tests for new functionality
   - Update documentation if needed

3. **Run quality checks**
   ```bash
   python dev.py check --strict    # Comprehensive checks
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

### Code Standards

- **Python**: 3.9+ compatibility required
- **Formatting**: Automatic with `ruff format`
- **Linting**: Must pass `ruff check` 
- **Type checking**: Full mypy compatibility required
- **Testing**: Maintain >90% test coverage

### Running Tests

```bash
# All tests
python dev.py test

# With coverage  
python dev.py test --coverage

# Specific test file
pytest tests/unit/test_specific.py

# Visual tests (generates screenshots)
pytest tests/ -m screenshot
```

### Development Commands

Choose your preferred command runner:

```bash
# Python script (recommended - works everywhere)
python dev.py check        # Basic quality checks
python dev.py check --full # Comprehensive checks  
python dev.py test         # Run tests
python dev.py format       # Format code
python dev.py clean        # Clean generated files

# Make (traditional)
make check
make test
make format

# Just (modern, if installed)
just check  
just test
just format
```

## Contributing Guidelines

### Bug Reports

Use the bug report template and include:
- textual-snapshots version
- Python version and OS
- Clear reproduction steps
- Expected vs actual behavior
- Error logs if applicable

### Feature Requests

Use the feature request template and include:
- Problem statement
- Proposed solution
- Usage examples
- Alternatives considered

### Pull Requests

1. **Link to an issue** - All PRs should address an existing issue
2. **Write clear commit messages** - Use conventional commit format
3. **Add tests** - New features need corresponding tests
4. **Update documentation** - Keep docs in sync with changes
5. **Pass all checks** - CI must pass before merge

### Commit Message Format

We follow conventional commits:

```
type(scope): description

feat(cli): add new capture command
fix(api): resolve screenshot timeout issue  
docs(readme): update installation instructions
test(core): add unit tests for validation
```

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `style`, `chore`

## Code Organization

```
textual-snapshots/
├── src/textual_snapshots/    # Main package
│   ├── __init__.py          # Public API
│   ├── capture.py           # Screenshot capture
│   ├── cli.py              # Command line interface
│   ├── comparison.py       # Image comparison
│   └── ...
├── tests/                   # Test suite
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests  
│   └── conftest.py         # Pytest configuration
├── README.md               # Project overview
├── GETTING_STARTED.md      # Getting started guide
└── API_REFERENCE.md        # Complete API documentation
```

## Testing Guidelines

### Test Types

- **Unit tests**: Fast, isolated, test individual functions
- **Integration tests**: Test component interactions
- **Visual tests**: Capture and compare screenshots
- **CLI tests**: Test command-line interface

### Writing Tests

```python
# Unit test example
import pytest
from textual_snapshots import capture_app_screenshot

@pytest.mark.asyncio
async def test_basic_capture():
    result = await capture_app_screenshot(TestApp(), context="test")
    assert result.success
    assert result.screenshot_path.exists()

# Visual test example  
@pytest.mark.screenshot
@pytest.mark.asyncio
async def test_visual_regression():
    result = await capture_app_screenshot(TestApp(), context="homepage")
    assert result.success
    # Visual comparison with baseline would happen in CI
```

### Test Markers

- `@pytest.mark.asyncio` - Async test
- `@pytest.mark.screenshot` - Generates screenshots  
- `@pytest.mark.slow` - Long-running test
- `@pytest.mark.integration` - Integration test

## Documentation

### Adding Documentation

- **API changes**: Update docstrings and API_REFERENCE.md
- **New features**: Add examples to GETTING_STARTED.md
- **CLI changes**: Update command documentation
- **Breaking changes**: Update migration notes

### Documentation Style

- Use clear, concise language
- Include practical examples
- Test all code examples
- Link related concepts

## Release Process

Releases are handled by maintainers:

1. Version bump in `pyproject.toml`
2. Update CHANGELOG.md
3. Tag release and push
4. GitHub Actions builds and publishes to PyPI

## Getting Help

- **Questions**: [GitHub Discussions](https://github.com/testinator-dev/textual-snapshots/discussions)
- **Bugs**: [GitHub Issues](https://github.com/testinator-dev/textual-snapshots/issues)
- **Chat**: [Textual Discord](https://discord.gg/Enf6Z3qhVr) #testing channel

## Code of Conduct

Be respectful, inclusive, and constructive. We're all here to build better tools together.

---

**Thank you for contributing to textual-snapshots!** 🎉