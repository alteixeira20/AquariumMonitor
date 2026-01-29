# AquariumMonitor — root workflow

GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
RED := \033[0;31m
RESET := \033[0m
BOLD := \033[1m

BACKEND_DIR := apps/backend
FRONTEND_DIR := apps/frontend

.PHONY: help
help:
	@echo "${BOLD}AquariumMonitor${RESET} — root tasks"
	@echo ""
	@echo "${BOLD}Backend${RESET}"
	@echo "  ${GREEN}make backend-dev${RESET}         Run backend dev server"
	@echo "  ${GREEN}make backend-test${RESET}        Run backend tests"
	@echo "  ${GREEN}make backend-test-sqlite${RESET} Run backend tests on SQLite"
	@echo "  ${GREEN}make backend-format${RESET}      Format backend (black)"
	@echo "  ${GREEN}make backend-lint${RESET}        Lint backend (ruff)"
	@echo ""
	@echo "${BOLD}Frontend${RESET}"
	@echo "  ${BLUE}make frontend-dev${RESET}        Run frontend dev server"
	@echo "  ${BLUE}make frontend-build${RESET}      Build frontend"
	@echo "  ${BLUE}make frontend-test${RESET}       Run frontend tests"
	@echo ""
	@echo "${BOLD}Infra${RESET}"
	@echo "  ${YELLOW}make docker-up${RESET}           Start containers"
	@echo "  ${YELLOW}make docker-down${RESET}         Stop containers"

backend-dev:
	@$(MAKE) -C $(BACKEND_DIR) dev

backend-test:
	@$(MAKE) -C $(BACKEND_DIR) test

backend-test-sqlite:
	@$(MAKE) -C $(BACKEND_DIR) test-sqlite

backend-format:
	@$(MAKE) -C $(BACKEND_DIR) format

backend-lint:
	@$(MAKE) -C $(BACKEND_DIR) lint

frontend-dev:
	@$(MAKE) -C $(FRONTEND_DIR) dev

frontend-build:
	@$(MAKE) -C $(FRONTEND_DIR) build

frontend-test:
	@$(MAKE) -C $(FRONTEND_DIR) test

docker-up:
	@docker compose -f infra/docker-compose.sqlite.yml up -d --build

docker-down:
	@docker compose -f infra/docker-compose.sqlite.yml down
