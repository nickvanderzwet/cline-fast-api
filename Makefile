.PHONY: help install install-dev test lint format check clean docker-build docker-up docker-down

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	pip install -r requirements.txt

install-dev: ## Install development dependencies
	pip install -r requirements/dev.txt
	pre-commit install

test: ## Run tests
	pytest

test-cov: ## Run tests with coverage
	pytest --cov=app --cov-report=html --cov-report=term-missing

lint: ## Run linting
	ruff check .
	mypy .

format: ## Format code
	ruff format .
	ruff check --fix .

check: ## Run all checks (lint + test)
	make lint
	make test

clean: ## Clean up temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .coverage htmlcov/ .pytest_cache/ .mypy_cache/ .ruff_cache/

docker-build: ## Build Docker containers
	cd docker && docker compose build

docker-up: ## Start Docker containers
	cd docker && docker compose up -d

docker-down: ## Stop Docker containers
	cd docker && docker compose down

docker-logs: ## Show Docker logs
	cd docker && docker compose logs -f

run-local: ## Run the application locally
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev: ## Start development environment
	make install-dev
	make docker-up
	@echo "Development environment ready!"
	@echo "API will be available at: http://localhost:8000"
	@echo "API docs at: http://localhost:8000/docs"
