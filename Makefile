# Timetable Builder - Development Makefile
# ========================================
#
# Usage:
#   make install      - Install package in development mode
#   make test         - Run tests
#   make lint         - Run linters
#   make format       - Format code
#   make build        - Build package
#   make clean        - Clean build artifacts
#   make docker-build - Build Docker image
#   make help         - Show this help

.PHONY: help install install-dev install-all test test-cov lint format typecheck clean build docker-build docker-run

# Default target
.DEFAULT_GOAL := help

# Project variables
PYTHON := python3
PIP := pip
PROJECT_NAME := timetable
SRC_DIR := src/$(PROJECT_NAME)
TESTS_DIR := tests
DOCKER_IMAGE := $(PROJECT_NAME):latest
REGISTRY := ghcr.io/sujith-eag/timetable-builder

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)Timetable Builder - Available Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""

# ==================== Installation ====================

install: ## Install package in development mode
	$(PIP) install -e .

install-dev: ## Install package with development dependencies
	$(PIP) install -e ".[dev]"

install-api: ## Install package with API dependencies
	$(PIP) install -e ".[api]"

install-all: ## Install package with all dependencies
	$(PIP) install -e ".[all]"

# ==================== Testing ====================

test: ## Run tests
	pytest $(TESTS_DIR) -v

test-unit: ## Run unit tests only
	pytest $(TESTS_DIR)/unit -v

test-integration: ## Run integration tests only
	pytest $(TESTS_DIR)/integration -v

test-cov: ## Run tests with coverage
	pytest $(TESTS_DIR) --cov=$(SRC_DIR) --cov-report=term-missing --cov-report=html

test-fast: ## Run tests without slow tests
	pytest $(TESTS_DIR) -v -m "not slow"

# ==================== Code Quality ====================

lint: ## Run linters (ruff)
	ruff check $(SRC_DIR) $(TESTS_DIR)

lint-fix: ## Run linters and fix issues
	ruff check --fix $(SRC_DIR) $(TESTS_DIR)

format: ## Format code with ruff
	ruff format $(SRC_DIR) $(TESTS_DIR)

format-check: ## Check code formatting
	ruff format --check $(SRC_DIR) $(TESTS_DIR)

typecheck: ## Run type checking with mypy
	mypy $(SRC_DIR)

quality: lint typecheck ## Run all quality checks

# ==================== Building ====================

build: clean ## Build package
	$(PYTHON) -m build

build-wheel: ## Build wheel only
	$(PYTHON) -m build --wheel

clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf $(SRC_DIR)/__pycache__/
	rm -rf $(TESTS_DIR)/__pycache__/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

# ==================== Docker ====================

docker-build: ## Build Docker image
	docker build -t $(DOCKER_IMAGE) .

docker-run: ## Run Docker container
	docker run --rm -it $(DOCKER_IMAGE)

docker-run-data: ## Run Docker container with data volume (mount ./data directory)
	docker run --rm -it -v $(PWD)/data:/app/data -e TIMETABLE_DATA_DIR=/app/data $(DOCKER_IMAGE)

docker-shell: ## Open shell in Docker container
	docker run --rm -it $(DOCKER_IMAGE) /bin/bash

docker-compose-up: ## Start services with Docker Compose
	docker-compose up -d

docker-compose-down: ## Stop Docker Compose services
	docker-compose down

docker-compose-logs: ## Show Docker Compose logs
	docker-compose logs -f

# ==================== Development ====================

dev-setup: install-dev ## Complete development setup
	pre-commit install
	@echo "$(GREEN)Development environment ready!$(NC)"

# ==================== Documentation ====================

docs-serve: ## Serve documentation locally
	mkdocs serve

docs-build: ## Build documentation
	mkdocs build

# ==================== Release ====================

version: ## Show current version
	@$(PYTHON) -c "import timetable; print(timetable.__version__)"

check-dist: build ## Check distribution files
	twine check dist/*

test-install: build ## Test installation in temporary environment
	$(PYTHON) -m pip install --user --force-reinstall dist/*.whl
	@echo "$(GREEN)Testing CLI:$(NC)"
	timetable --version
	@echo "$(GREEN)Installation test successful!$(NC)"

publish: check-dist ## Publish to PyPI
	twine upload dist/*
