.PHONY: help install dev test lint clean dist format

# Default target
help: ## Show this help message
	@echo "mindflow-cli - Lightweight AI Knowledge Workflow Automation Engine"
	@echo ""
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'
	@echo ""

install: ## Install the project
	pip install .

dev: ## Install in development mode (editable)
	pip install -e .

test: ## Run tests
	python -m pytest tests/ -v --tb=short

test-cov: ## Run tests with coverage report
	python -m pytest tests/ -v --tb=short --cov=mindflow_cli --cov-report=term-missing

lint: ## Run code linting
	@if command -v flake8 > /dev/null 2>&1; then \
		echo "Running flake8..."; \
		flake8 mindflow_cli/ tests/; \
	else \
		echo "flake8 not found, skipping."; \
	fi
	@if command -v pylint > /dev/null 2>&1; then \
		echo "Running pylint..."; \
		pylint mindflow_cli/; \
	else \
		echo "pylint not found, skipping."; \
	fi

format: ## Format code with black/isort if available
	@if command -v black > /dev/null 2>&1; then \
		echo "Running black..."; \
		black mindflow_cli/ tests/; \
	else \
		echo "black not found, skipping."; \
	fi
	@if command -v isort > /dev/null 2>&1; then \
		echo "Running isort..."; \
		isort mindflow_cli/ tests/; \
	else \
		echo "isort not found, skipping."; \
	fi

clean: ## Clean build artifacts and cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	rm -rf build/ dist/ .coverage htmlcov/ 2>/dev/null || true
	@echo "Clean complete."

dist: ## Build distribution packages
	python -m build

check: lint test ## Run linting and tests

all: clean lint test dist ## Clean, lint, test, and build
