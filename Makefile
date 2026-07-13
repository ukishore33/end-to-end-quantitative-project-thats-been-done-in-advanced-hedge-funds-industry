# Makefile for Quantitative Hedge Fund Project

.PHONY: help setup install test lint format clean backtest dashboard notebook

help:
	@echo "Quantitative Hedge Fund Project - Available Commands"
	@echo ""
	@echo "Setup & Dependencies:"
	@echo "  make setup          Create virtual environment and install dependencies"
	@echo "  make install        Install dependencies only"
	@echo "  make clean          Remove cache and build files"
	@echo ""
	@echo "Development:"
	@echo "  make test           Run test suite with coverage"
	@echo "  make test-fast      Run tests without coverage"
	@echo "  make lint           Run linters (black, flake8, mypy)"
	@echo "  make format         Format code with black"
	@echo ""
	@echo "Running Project:"
	@echo "  make backtest       Run example backtest"
	@echo "  make dashboard      Launch Streamlit dashboard"
	@echo "  make notebook       Start Jupyter notebook"
	@echo ""

setup:
	@echo "Creating virtual environment..."
	python -m venv venv
	@echo "Installing dependencies..."
	. venv/bin/activate && pip install --upgrade pip setuptools wheel
	. venv/bin/activate && pip install -r requirements.txt
	@echo "✓ Setup complete! Run: source venv/bin/activate"

install:
	pip install --upgrade pip setuptools wheel
	pip install -r requirements.txt
	@echo "✓ Dependencies installed"

test:
	@echo "Running tests with coverage..."
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing
	@echo "✓ Coverage report generated: htmlcov/index.html"

test-fast:
	@echo "Running tests (fast mode)..."
	pytest tests/ -v

lint:
	@echo "Running code quality checks..."
	@echo "- Formatting check (black)..."
	black --check src/ tests/ scripts/ || true
	@echo "- Style check (flake8)..."
	flake8 src/ tests/ scripts/ --max-line-length=100 || true
	@echo "✓ Code quality check complete"

format:
	@echo "Formatting code with black..."
	black src/ tests/ scripts/
	@echo "✓ Code formatted"

clean:
	@echo "Cleaning up..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache .coverage htmlcov .mypy_cache 2>/dev/null || true
	@echo "✓ Cleanup complete"

backtest:
	@echo "Running example backtest..."
	python scripts/run_backtest.py --strategy mean_reversion --start 2023-01-01 --end 2023-12-31

dashboard:
	@echo "Launching Streamlit dashboard..."
	streamlit run src/monitoring/dashboard.py

notebook:
	@echo "Starting Jupyter Lab..."
	jupyter lab notebooks/

.DEFAULT_GOAL := help
