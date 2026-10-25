.PHONY: help install dev lint format typecheck test test-e2e test-integration \
        verify smoke bench build clean docker-up docker-down api ui web \
        verify-docs verify-docs-fast test-docs mutate-docs prove prove-fast \
        refs-extract refs-check refs-coverage refs-verify refs-verify-crops

help:            ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

install:         ## Editable install with dev extras
	pip install -e ".[dev]"
	pre-commit install

dev:             ## Smoke-check the workspace resolves
	python -m bridgecad

lint:            ## ruff lint
	ruff check .

format:          ## ruff format + autofix
	ruff format .
	ruff check --fix .

typecheck:       ## mypy
	mypy packages apps

test:            ## Unit tests
	pytest packages tests/unit -q

test-integration: ## Full pipeline
	pytest tests/integration -v

test-e2e:        ## 28 fixtures
	python tests/e2e/run_e2e.py

verify:          ## Acceptance verifiers
	python -m bridgecad verify

smoke:           ## Release gate
	python rc1_smoke.py

bench:           ## Benchmarks, 20% regression gate
	pytest tests/benchmarks --benchmark-only

api:             ## Run the API
	uvicorn bridgecad_api.main:app --reload --app-dir apps/api-gateway

ui:              ## Run the Streamlit console
	streamlit run apps/streamlit-ui/app.py

web:             ## Run the React console
	cd apps/web-console && npm run dev

docker-up:
	docker compose up -d

docker-down:
	docker compose down

build:           ## Build distributions
	python -m build

clean:
	rm -rf build dist *.egg-info .pytest_cache .mypy_cache .ruff_cache
	find . -name __pycache__ -type d -prune -exec rm -rf {} +

labels:          ## Create or update repo labels (needs gh, authenticated)
	python scripts/sync_labels.py

wing:             ## Wing geometry suite
	pytest tests/draw -v

wing-fast:        ## Skip visual baselines
	pytest tests/draw -v -m "draw and not visual"

wing-rebaseline:  ## Regenerate PNG baselines
	rm -f tests/draw/baselines/*.hash
	pytest tests/draw -m visual

wing-report:     ## Per-sheet review report (HTML + JSON)
	python scripts/wing_report.py --html site-wing/wing-report.html --json wing-report.json

wing-report-check: ## Report and fail on any structural failure
	python scripts/wing_report.py --check

wing-report-open:  ## Report, then open it
	python scripts/wing_report.py
	@python -c "import webbrowser,sys; webbrowser.open('site-wing/wing-report.html')"

prove-draw:      ## Prove the Wing suite catches broken geometry (16/16)
	python scripts/prove_draw_detection.py

prove-draw-fast: ## Critical geometry mutations only
	python scripts/prove_draw_detection.py --only G01,G02,G03,G05 --jobs 8

links:           ## Check external + internal links
	lychee --config .lychee.toml --no-progress '**/*.md'

docpaths:        ## Check paths referenced in code blocks
	python scripts/check_doc_paths.py

docs-check: links docpaths  ## Both

docs-serve:      ## Live docs site
	mkdocs serve

docs-build:      ## Strict build
	mkdocs build --strict

docs-clean:
	rm -rf site site-api docs/guide.md docs/index.md docs/contributing.md \
	       docs/changelog.md docs/security.md docs/code-of-conduct.md docs/docs-index.md

verify-docs:     ## Full documentation verification (JSON)
	python scripts/verify_docs.py --json

verify-docs-fast: ## Integrity + path gates only
	python scripts/verify_docs.py --only paths,integrity

test-docs:       ## Doc test suite, verbose
	pytest tests/docs -v

mutate-docs:     ## Gate self-tests only — proves the guards fire
	pytest tests/docs/test_gates_selfcheck.py -v

prove:           ## Prove every defect is detectable (17/17)
	python scripts/prove_detection.py

prove-fast:      ## Critical defects only
	python scripts/prove_detection.py --only D01,D02,D03,D04 --jobs 8

refs-extract:      ## Pull facts off references (text layer + OCR)
	python scripts/refs_extract.py

refs-check:        ## Fail if extracted/ is stale against raw/ or the pipeline
	python scripts/refs_extract.py --check

refs-coverage:     ## Write and print the coverage report
	python scripts/refs_coverage.py

refs-verify:       ## Show proposed values with citations
	python scripts/refs_verify.py

refs-verify-crops: ## Write bbox crops so a human verifies OCR against pixels
	python scripts/refs_verify.py --crop
