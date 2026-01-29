# **************************************************************************** #
#                              Automated Makefile                              #
# **************************************************************************** #

# Visual formatting
BOLD    := \033[1m
RESET   := \033[0m
YELLOW  := \033[0;33m

# Declarations - Python / Virtualenv

PYTHON      := python3
VENV        := .venv
VENV_BIN    := $(VENV)/bin

PIP         := $(VENV_BIN)/pip
UVICORN     := $(VENV_BIN)/uvicorn
PYTEST      := $(VENV_BIN)/pytest
RUFF        := $(VENV_BIN)/ruff
BLACK       := $(VENV_BIN)/black

# Application Settings

APP_MODULE  := app.main:app
HOST        := 0.0.0.0
PORT        := 8000

# Docker Settings

IMAGE_NAME  := aquariummonitor/backend

INSTALL_STAMP := $(VENV)/.install.stamp

# Phony Declarations

.PHONY: help venv install deps dev run test test-sqlite lint format check docker-build docker-run docker-run-volume clean clean-venv db-upgrade seed

# ------------------------------
# Help Menu
# ------------------------------

help:
	@echo "$(YELLOW)Available commands:$(RESET)"
	@echo "  $(BOLD)make install$(RESET)       - Setup virtual environment + dependencies"
	@echo "  $(BOLD)make deps$(RESET)          - Ensure dependencies are installed (silent if up-to-date)"
	@echo "  $(BOLD)make dev$(RESET)           - Run API in development mode (reload)"
	@echo "  $(BOLD)make run$(RESET)           - Run API normally"
	@echo "  $(BOLD)make test$(RESET)          - Run test suite"
	@echo "  $(BOLD)make test-sqlite$(RESET)   - Run tests with SQLite backend"
	@echo "  $(BOLD)make db-upgrade$(RESET)    - Run Alembic migrations"
	@echo "  $(BOLD)make seed$(RESET)          - Seed admin user (reads SEED_ADMIN_* env)"
	@echo "  $(BOLD)make format$(RESET)        - Format ALL files with Black"
	@echo "  $(BOLD)make lint$(RESET)          - Lint ALL files with Ruff"
	@echo "  $(BOLD)make check$(RESET)         - Run lint + test"
	@echo "  $(BOLD)make clean$(RESET)         - Remove Python caches"
	@echo "  $(BOLD)make clean-venv$(RESET)    - Delete virtual environment"
	@echo "  $(BOLD)make docker-build$(RESET)  - Build Docker image"
	@echo "  $(BOLD)make docker-run$(RESET)    - Run Docker container"

# ------------------------------
# Virtual Environment
# ------------------------------

venv:
	@if ! command -v $(PYTHON) >/dev/null 2>&1; then \
		echo "$(BOLD)python3 not found. Please install Python 3.12+ and rerun.$(RESET)"; \
		exit 1; \
	fi
	@python_ok=$$($(PYTHON) -c 'import sys; print(0 if sys.version_info >= (3,12) else 1)'); \
	if [ "$$python_ok" -ne 0 ]; then \
		python_ver=$$($(PYTHON) -c 'import sys; print(".".join(map(str, sys.version_info[:3])))'); \
		echo "$(BOLD)Python $$python_ver detected. Python 3.12+ required. Please upgrade and rerun.$(RESET)"; \
		exit 1; \
	fi
	@if [ ! -d $(VENV) ]; then \
		echo "$(BOLD)==> Creating virtual environment…$(RESET)"; \
		if ! $(PYTHON) -m venv $(VENV) >/dev/null 2>&1; then \
			echo "$(BOLD)==> python3-venv missing or venv failed. Attempting install (sudo required)…$(RESET)"; \
			sudo apt-get update && sudo apt-get install -y python3-venv python3-pip || { echo "$(BOLD)python3-venv install failed. Please install manually.$(RESET)"; exit 1; }; \
			$(PYTHON) -m venv $(VENV) || { echo "$(BOLD)venv creation failed. Please check Python installation.$(RESET)"; exit 1; }; \
		fi; \
		echo "$(BOLD)==> Virtual environment created at $(VENV).$(RESET)"; \
	else \
		echo "$(BOLD)==> Virtual environment already present at $(VENV); skipping creation.$(RESET)"; \
	fi

install: $(INSTALL_STAMP)

deps: $(INSTALL_STAMP)

$(INSTALL_STAMP): requirements.txt | venv
	@echo "$(BOLD)==> Installing dependencies…$(RESET)"
	@PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_PYTHON_VERSION_WARNING=1 \
		$(VENV_BIN)/python -m pip install --upgrade pip --no-input --quiet \
		|| echo "$(YELLOW)Skipping pip upgrade (offline or blocked).$(RESET)"
	@PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_PYTHON_VERSION_WARNING=1 \
		$(VENV_BIN)/python -m pip install -r requirements.txt --quiet
	@touch $(INSTALL_STAMP)

db-upgrade: deps
	@echo "$(BOLD)==> Running Alembic migrations…$(RESET)"
	$(VENV_BIN)/alembic upgrade head

seed: deps
	@echo "$(BOLD)==> Seeding admin user…$(RESET)"
	$(VENV_BIN)/python scripts/seed_user.py

# ------------------------------
# Run API
# ------------------------------

dev: deps
	@echo "$(BOLD)==> Starting development server…$(RESET)"
	$(UVICORN) $(APP_MODULE) --host $(HOST) --port $(PORT) --reload

run: deps
	@echo "$(BOLD)==> Starting API server…$(RESET)"
	$(UVICORN) $(APP_MODULE) --host $(HOST) --port $(PORT)

# ------------------------------
# Tests + Lint + Format
# ------------------------------

test: deps
	@echo "$(BOLD)==> Running tests…$(RESET)"
	@mkdir -p logs
	@if [ -f logs/test.log ]; then \
		printf "$(YELLOW)logs/test.log exists. Delete it and continue? [y/N] $(RESET)"; \
		read -r reply; \
		case "$$reply" in \
			[yY]|[yY][eE][sS]) rm -f logs/test.log ;; \
			*) echo "$(BOLD)Aborted.$(RESET)"; exit 1 ;; \
		esac; \
	fi
	@ENVIRONMENT=test STORAGE_BACKEND=memory PYTHONPATH=. $(PYTEST) -m "not sqlite_only and not db_seed_only"

test-sqlite: deps
	@echo "$(BOLD)==> Running tests against SQLite backend…$(RESET)"
	@mkdir -p data logs
	@if [ -f data/test.db ]; then \
		echo "$(BOLD)==> Found existing data/test.db; removing it for a clean run…$(RESET)"; \
		rm -f data/test.db; \
	fi
	@ENVIRONMENT=test STORAGE_BACKEND=sqlite DATABASE_URL=sqlite:///./data/test.db PYTHONPATH=. $(PYTEST) -m "not memory_only and not db_seed_only"
	@ENVIRONMENT=test STORAGE_BACKEND=sqlite DATABASE_URL=sqlite:///./data/test.db PYTHONPATH=. $(PYTEST) -m "db_seed_only"
	@echo "$(BOLD)==> SQLite test database written to $(YELLOW)data/test.db$(RESET)$(BOLD) with seeded sample data.$(RESET)"

lint: deps
	@echo "$(BOLD)==> Running Ruff linter on all files…$(RESET)"
	$(RUFF) check .

format: deps
	@echo "$(BOLD)==> Formatting all code with Black…$(RESET)"
	-$(RUFF) check --fix .
	$(BLACK) .

check: lint test

# ------------------------------
# Docker
# ------------------------------

docker-build:
	@echo "$(BOLD)==> Building Docker image…$(RESET)"
	docker build -t $(IMAGE_NAME) .

docker-run:
	@echo "$(BOLD)==> Running Docker container…$(RESET)"
	docker run --rm -p $(PORT):$(PORT) --env-file .env $(IMAGE_NAME)

docker-run-volume:
	@echo "$(BOLD)==> Running Docker container with ./data mounted for persistence…$(RESET)"
	docker run --rm -p $(PORT):$(PORT) --env-file .env -v "$(PWD)/data:/app/data" $(IMAGE_NAME)

# ------------------------------
# Cleanup
# ------------------------------

clean:
	@echo "$(BOLD)==> Cleaning Python caches…$(RESET)"
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .pytest_cache

clean-venv:
	@echo "$(BOLD)==> Removing virtual environment…$(RESET)"
	rm -rf $(VENV)
