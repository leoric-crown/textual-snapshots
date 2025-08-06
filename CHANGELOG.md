# Changelog

All notable changes to textual-snapshots will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of textual-snapshots
- Professional visual testing for Textual applications
- Zero-configuration screenshot capture with auto-discovery
- CLI tools: `capture`, `compare`, `migrate`, `convert`
- Rich interaction support (clicks, typing, keyboard events)
- Plugin system for extensible functionality
- Migration tools from pytest-textual-snapshot
- CI/CD integration examples and workflows
- Comprehensive API documentation

### Features
- **Screenshot Capture**: Automated visual testing for Textual applications
- **Format Support**: SVG (default) and PNG output with conversion tools
- **Interactive Testing**: Record user interactions (clicks, typing, etc.)
- **Auto-Discovery**: Automatically find and test Textual apps in your project
- **Migration Tools**: Seamless migration from pytest-textual-snapshot
- **Plugin Architecture**: Extensible system for custom validation and workflows
- **Professional CLI**: Rich output with tables, progress indicators, and error handling
- **CI/CD Ready**: GitHub Actions examples and batch processing support

### Technical
- Python 3.9+ compatibility
- Type-safe with comprehensive mypy coverage
- Async/await support throughout
- Rich console output and error reporting
- Comprehensive test suite with >90% coverage

## [0.1.0] - 2025-08-06

### Added
- Initial public release
- Core screenshot capture functionality
- CLI interface with professional commands
- Migration tools from pytest-textual-snapshot
- Comprehensive documentation and examples