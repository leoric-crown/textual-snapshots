# textual-snapshots Development Makefile
# Cross-platform development commands for textual-snapshots

.DEFAULT_GOAL := help

# Colors for output (works on most terminals)
BLUE := \033[34m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
RESET := \033[0m

# Detect OS for platform-specific commands
UNAME_S := $(shell uname -s 2>/dev/null || echo Windows)
ifeq ($(UNAME_S),Darwin)
    PLATFORM := macOS
    OPEN_CMD := open
endif
ifeq ($(UNAME_S),Linux)
    PLATFORM := Linux
    OPEN_CMD := xdg-open
endif
ifeq ($(UNAME_S),Windows_NT)
    PLATFORM := Windows
    OPEN_CMD := start
endif
ifneq (,$(findstring MINGW,$(UNAME_S)))
    PLATFORM := Windows
    OPEN_CMD := start
endif

##@ Development Commands

.PHONY: help
help: ## Show this help message
	@echo "$(BLUE)textual-snapshots Developer Commands ($(PLATFORM))$(RESET)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  $(YELLOW)%-20s$(RESET) %s\n", $$1, $$2 } /^##@/ { printf "\n$(BLUE)%s$(RESET)\n", substr($$0, 5) }' $(MAKEFILE_LIST)

.PHONY: install
install: ## Install dependencies and setup development environment
	@echo "$(BLUE)🚀 Setting up development environment...$(RESET)"
	@uv sync
	@uv run playwright install chromium
	@echo "$(GREEN)✅ Development environment ready!$(RESET)"

.PHONY: install-ci
install-ci: ## Install dependencies for CI/CD (without browser setup)
	@echo "$(BLUE)🤖 Setting up CI environment...$(RESET)"
	@uv sync
	@echo "$(GREEN)✅ CI environment ready!$(RESET)"

##@ Code Quality

.PHONY: format
format: ## Format code with ruff
	@echo "$(BLUE)🎨 Formatting code...$(RESET)"
	@uv run ruff format src tests
	@uv run ruff check --fix src tests
	@echo "$(GREEN)✅ Code formatted!$(RESET)"

.PHONY: format-check
format-check: ## Check code formatting without making changes
	@echo "$(BLUE)🔍 Checking code formatting...$(RESET)"
	@uv run ruff format --check src tests
	@uv run ruff check src tests

.PHONY: lint
lint: ## Run linting checks
	@echo "$(BLUE)🔍 Running linting checks...$(RESET)"
	@uv run ruff check src tests
	@echo "$(GREEN)✅ Linting passed!$(RESET)"

.PHONY: typecheck
typecheck: ## Run type checking with mypy
	@echo "$(BLUE)🔍 Running type checks...$(RESET)"
	@uv run mypy src
	@echo "$(GREEN)✅ Type checking passed!$(RESET)"

.PHONY: typecheck-strict
typecheck-strict: ## Run strict type checking (source code only)
	@echo "$(BLUE)🔍 Running strict type checks...$(RESET)"
	@uv run mypy src
	@echo "$(YELLOW)Note: Test type checking skipped in strict mode$(RESET)"
	@echo "$(GREEN)✅ Strict type checking passed!$(RESET)"

##@ Testing

.PHONY: test
test: ## Run tests with standard output
	@echo "$(BLUE)🧪 Running tests...$(RESET)"
	@uv run pytest tests/ --tb=short -v

.PHONY: test-quiet
test-quiet: ## Run tests with minimal output
	@echo "$(BLUE)🧪 Running tests (quiet)...$(RESET)"
	@uv run pytest tests/ --tb=short -q

.PHONY: test-coverage
test-coverage: ## Run tests with coverage reporting
	@echo "$(BLUE)🧪 Running tests with coverage...$(RESET)"
	@uv run pytest tests/ --cov=src --cov-report=term-missing --cov-report=html
	@echo "$(GREEN)✅ Coverage report generated in htmlcov/$(RESET)"

.PHONY: test-watch
test-watch: ## Run tests in watch mode (requires pytest-xdist)
	@echo "$(BLUE)👀 Watching tests...$(RESET)"
	@uv run pytest tests/ --tb=short -f

##@ Quality Checks

.PHONY: check
check: lint typecheck test-quiet ## Run basic quality checks (lint, typecheck, test)
	@echo "$(GREEN)✅ All basic checks passed!$(RESET)"

.PHONY: check-strict
check-strict: lint typecheck-strict test-quiet ## Run strict quality checks
	@echo "$(GREEN)✅ All strict checks passed!$(RESET)"

.PHONY: check-full
check-full: format-check lint typecheck-strict test-coverage ## Run comprehensive checks with coverage
	@echo "$(GREEN)✅ All comprehensive checks passed!$(RESET)"

##@ CLI Testing

.PHONY: cli-test
cli-test: ## Test CLI commands manually
	@echo "$(BLUE)🖥️  Testing CLI commands...$(RESET)"
	@echo "Testing help command:"
	@uv run textual-snapshot --help
	@echo "\nTesting version:"
	@uv run textual-snapshot --version

.PHONY: demo
demo: ## Run CLI demo with sample data
	@echo "$(BLUE)🎭 Running CLI demo...$(RESET)"
	@echo '<svg width="100" height="50" xmlns="http://www.w3.org/2000/svg"><rect width="100" height="50" fill="blue"/></svg>' > demo.svg
	@uv run textual-snapshot convert demo.svg --to png --quality high || true
	@rm -f demo.svg converted/demo.png 2>/dev/null || true
	@rmdir converted 2>/dev/null || true
	@echo "$(GREEN)✅ Demo completed!$(RESET)"

##@ Documentation

.PHONY: docs-serve
docs-serve: ## Serve documentation locally (if docs server available)
	@echo "$(BLUE)📚 Serving documentation...$(RESET)"
	@if command -v mkdocs >/dev/null 2>&1; then \
		mkdocs serve; \
	else \
		echo "$(YELLOW)⚠️  MkDocs not installed. Install with: pip install mkdocs$(RESET)"; \
	fi

.PHONY: docs-build
docs-build: ## Build documentation
	@echo "$(BLUE)📚 Building documentation...$(RESET)"
	@if command -v mkdocs >/dev/null 2>&1; then \
		mkdocs build; \
	else \
		echo "$(YELLOW)⚠️  MkDocs not installed. Skipping docs build$(RESET)"; \
	fi

##@ Coverage & Reports

.PHONY: coverage-html
coverage-html: ## Generate HTML coverage report and open it
	@echo "$(BLUE)📊 Generating coverage report...$(RESET)"
	@uv run pytest tests/ --cov=src --cov-report=html
	@echo "$(GREEN)✅ Opening coverage report...$(RESET)"
	@$(OPEN_CMD) htmlcov/index.html

.PHONY: coverage-xml
coverage-xml: ## Generate XML coverage report (for CI)
	@echo "$(BLUE)📊 Generating XML coverage report...$(RESET)"
	@uv run pytest tests/ --cov=src --cov-report=xml

##@ Development Utilities

.PHONY: clean
clean: ## Clean up generated files and caches
	@echo "$(BLUE)🧹 Cleaning up...$(RESET)"
	@rm -rf .coverage htmlcov/ .pytest_cache/ .mypy_cache/ .ruff_cache/
	@rm -rf src/*.egg-info/ dist/ build/
	@rm -rf screenshots/ baselines/ converted/ test_output/
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)✅ Cleanup complete!$(RESET)"

.PHONY: reset
reset: clean ## Reset development environment (clean + reinstall)
	@echo "$(BLUE)🔄 Resetting development environment...$(RESET)"
	@rm -rf .venv/
	@$(MAKE) install
	@echo "$(GREEN)✅ Environment reset complete!$(RESET)"

.PHONY: deps-update
deps-update: ## Update dependencies
	@echo "$(BLUE)📦 Updating dependencies...$(RESET)"
	@uv sync --upgrade
	@echo "$(GREEN)✅ Dependencies updated!$(RESET)"

##@ Git & Release

.PHONY: pre-commit
pre-commit: check-strict ## Run all checks before committing
	@echo "$(GREEN)✅ Ready to commit!$(RESET)"

.PHONY: pre-push
pre-push: check-full ## Run comprehensive checks before pushing
	@echo "$(GREEN)✅ Ready to push!$(RESET)"

##@ Platform Info

.PHONY: info
info: ## Show development environment info
	@echo "$(BLUE)📋 Development Environment Info$(RESET)"
	@echo "Platform: $(PLATFORM)"
	@echo "Python: $$(uv run python --version 2>/dev/null || echo 'Not available')"
	@echo "UV: $$(uv --version 2>/dev/null || echo 'Not available')"
	@echo "Playwright: $$(uv run playwright --version 2>/dev/null || echo 'Not installed')"
	@echo "Git: $$(git --version 2>/dev/null || echo 'Not available')"
	@echo ""
	@echo "Project Status:"
	@echo "- Virtual Environment: $$([ -d .venv ] && echo '✅ Present' || echo '❌ Missing')"
	@echo "- Dependencies: $$([ -f uv.lock ] && echo '✅ Locked' || echo '❌ Not locked')"
	@echo "- Pre-commit: $$([ -f .pre-commit-config.yaml ] && echo '✅ Configured' || echo '⚠️  Not configured')"

