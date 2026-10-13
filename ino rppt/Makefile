SHELL := /bin/bash
.ONESHELL:
.SILENT: help

PYTHON ?= python3
PIP ?= pip
UV ?= uv

ROOT_DIR := $(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))
PACKAGES_DIR := $(ROOT_DIR)/packages
APPS_DIR := $(ROOT_DIR)/apps

.PHONY: help install install-dev lint format typecheck test test-e2e bench \
        build clean dev api cli streamlit console scaffold-plugin tree \
        docker-up docker-down docs

help: ## Show this help
	@awk 'BEGIN {FS = ":.*##"; printf "\n\033[1mBridgeCAD Enterprise Suite\033[0m — Makefile targets\n\n"} \
		/^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2 } \
		END { print "" }' $(MAKEFILE_LIST)

# ---------------------------------------------------------------------------
# Environment / install
# ---------------------------------------------------------------------------

install: ## Install all runtime dependencies
	$(PIP) install --upgrade pip
	@for pkg in $(PACKAGES_DIR)/*/pyproject.toml; do \
		echo "► installing $${pkg%/pyproject.toml}"; \
		$(PIP) install -e "$${pkg%/pyproject.toml}"; \
	done
	@for app in $(APPS_DIR)/*/pyproject.toml; do \
		echo "► installing $${app%/pyproject.toml}"; \
		$(PIP) install -e "$${app%/pyproject.toml}"; \
	done

install-dev: install ## Install + dev tools
	$(PIP) install ruff mypy pytest pytest-cov pytest-benchmark pre-commit
	pre-commit install || true

# ---------------------------------------------------------------------------
# Quality
# ---------------------------------------------------------------------------

lint: ## Run ruff linter on all packages and apps
	ruff check $(PACKAGES_DIR) $(APPS_DIR) scripts/

format: ## Auto-format all Python code
	ruff format $(PACKAGES_DIR) $(APPS_DIR) scripts/

typecheck: ## Run mypy type-check
	mypy $(PACKAGES_DIR)/bridgecad_core \
	     $(PACKAGES_DIR)/bridgecad_io \
	     $(PACKAGES_DIR)/bridgecad_bill \
	     $(PACKAGES_DIR)/bridgecad_qa

test: ## Run unit + integration tests
	pytest tests/ -x --ignore=tests/e2e --ignore=tests/benchmarks

test-e2e: ## Run end-to-end fixtures
	pytest tests/e2e -v

bench: ## Run benchmark suite
	pytest tests/benchmarks --benchmark-autosave

# ---------------------------------------------------------------------------
# Build / clean
# ---------------------------------------------------------------------------

build: ## Build all packages (wheel + sdist)
	@for pkg in $(PACKAGES_DIR)/*/pyproject.toml; do \
		(cd "$${pkg%/pyproject.toml}" && $(PYTHON) -m build); \
	done

clean: ## Remove build artifacts, caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf dist/ build/ htmlcov/ .coverage 2>/dev/null || true

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

dev: ## Run CLI version health check
	$(PYTHON) -m bridgecad_cli version

api: ## Run FastAPI API gateway on :8000
	cd $(APPS_DIR)/api-gateway && $(PYTHON) -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

cli: ## Run CLI console (pass args after: make cli -- --help)
	$(PYTHON) -m bridgecad_cli $(filter-out $@,$(MAKECMDGOALS))

streamlit: ## Run Streamlit Ultimate UI on :8501
	cd $(APPS_DIR)/streamlit-ui && streamlit run app.py --server.port 8501

console: ## Run React web-console dev server on :5173
	cd $(APPS_DIR)/web-console && npm install && npm run dev

# ---------------------------------------------------------------------------
# Scaffolding helpers
# ---------------------------------------------------------------------------

scaffold-plugin: ## Scaffold a new plugin (usage: make scaffold-plugin NAME=flyover)
	$(PYTHON) scripts/scaffold_plugin.py $(NAME)

tree: ## Print project tree excluding caches
	tree -L 3 -I '__pycache__|*.egg-info|node_modules|.mypy_cache|.ruff_cache|.pytest_cache' . || \
	find . -maxdepth 3 -not -path '*/\.*' -not -path '*__pycache__*' -not -path '*.egg-info*' -print

# ---------------------------------------------------------------------------
# Docker
# ---------------------------------------------------------------------------

docker-up: ## docker-compose up with full stack (db + cache + storage + api)
	docker compose up -d --build

docker-down: ## docker-compose down + remove volumes? (no volumes)
	docker compose down

# ---------------------------------------------------------------------------
# Docs
# ---------------------------------------------------------------------------

docs: ## Build Sphinx + MkDocs hybrid docs
	cd docs && make html 2>/dev/null || echo "docs scaffolded; run sphinx-quickstart first"
