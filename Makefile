# Common tasks for maintaining the skills. Run `make help` for the list.
# Every target works without make: see docs/tooling.md for the raw commands.

PYTHON       ?= python3
SKILLKIT     := $(PYTHON) scripts/skillkit.py
MARKDOWNLINT := npx --yes markdownlint-cli2@0.24.0
BASE         ?= origin/main

.DEFAULT_GOAL := help
.PHONY: help install validate catalog versions test lint format check package release-plan plugin-validate new clean

help: ## Show this help
	@awk 'BEGIN {FS = ":.*## "} /^[a-zA-Z_-]+:.*## / {printf "  %-16s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dev dependencies and the git hooks
	$(PYTHON) -m pip install -r requirements-dev.txt
	$(PYTHON) -m pre_commit install --install-hooks -t pre-commit -t pre-push

validate: ## Validate skills, marketplace, links and catalog
	$(SKILLKIT) validate

catalog: ## Regenerate the catalog tables and sync marketplace.json
	$(SKILLKIT) catalog

versions: ## Check version bumps against BASE (default origin/main)
	$(SKILLKIT) check-versions --base $(BASE)

test: ## Run the skillkit tests
	$(PYTHON) -m pytest -q

lint: ## Lint Markdown and Python
	$(MARKDOWNLINT)
	$(PYTHON) -m ruff check scripts tests
	$(PYTHON) -m ruff format --check scripts tests

format: ## Auto-format and auto-fix Python (Markdown is fixed by hand; see docs/tooling.md)
	$(PYTHON) -m ruff format scripts tests
	$(PYTHON) -m ruff check --fix scripts tests

check: validate versions test lint ## Everything CI runs on a pull request

package: ## Build release zips into dist/
	$(SKILLKIT) package

release-plan: ## Show which skill versions the next merge to main would release
	$(SKILLKIT) release --dry-run

plugin-validate: ## Validate the marketplace with Claude Code (needs the claude CLI)
	claude plugin validate . --strict

new: ## Scaffold a skill: make new DOMAIN=fixed-income NAME=bond-relative-value
	@test -n "$(DOMAIN)" -a -n "$(NAME)" || { echo "usage: make new DOMAIN=<domain> NAME=<skill-name>"; exit 2; }
	$(SKILLKIT) new $(DOMAIN) $(NAME)

clean: ## Remove build output and caches
	rm -rf dist .pytest_cache .ruff_cache
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
