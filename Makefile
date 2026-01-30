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
	@echo "${BOLD}Most used${RESET}"
	@echo "  ${GREEN}make dev${RESET}                Start backend in dev mode"
	@echo "  ${YELLOW}make prod${RESET}               Start production stack (SQLite)"
	@echo "  ${YELLOW}make prod-sim${RESET}           Start production stack + simulator"
	@echo "  ${GREEN}make test${RESET}               Run backend tests (memory)"
	@echo "  ${GREEN}make test-sqlite${RESET}        Run backend tests (SQLite)"
	@echo "  ${YELLOW}make stop${RESET}               Stop all containers"
	@echo ""
	@echo "${BOLD}Backend${RESET}"
	@echo "  ${GREEN}make backend-dev${RESET}         Run backend dev server"
	@echo "  ${GREEN}make backend-test${RESET}        Run backend tests"
	@echo "  ${GREEN}make backend-test-sqlite${RESET} Run backend tests on SQLite"
	@echo "  ${GREEN}make backend-format${RESET}      Format backend (black)"
	@echo "  ${GREEN}make backend-lint${RESET}        Lint backend (ruff)"
	@echo ""
	@echo "${BOLD}Simulator${RESET}"
	@echo "  ${BLUE}make simulator-setup${RESET}     Prepare simulator env + config"
	@echo "  ${BLUE}make simulator-up${RESET}        Run backend + simulator (SQLite)"
	@echo "  ${BLUE}make simulator-down${RESET}      Stop simulator stack"
	@echo ""
	@echo "${BOLD}Frontend${RESET}"
	@echo "  ${BLUE}make frontend-dev${RESET}        Run frontend dev server"
	@echo "  ${BLUE}make frontend-build${RESET}      Build frontend"
	@echo "  ${BLUE}make frontend-test${RESET}       Run frontend tests"
	@echo ""
	@echo "${BOLD}Infra${RESET}"
	@echo "  ${YELLOW}make docker-up${RESET}           Start containers"
	@echo "  ${YELLOW}make docker-down${RESET}         Stop containers"
	@echo "  ${YELLOW}make docker-up-sim${RESET}       Start containers + simulator"

dev:
	@echo "${BOLD}==> Starting backend in dev mode${RESET}"
	@$(MAKE) -C $(BACKEND_DIR) dev

prod:
	@echo "${BOLD}==> Starting production stack (SQLite)${RESET}"
	@$(MAKE) docker-up

prod-sim: simulator-setup
	@echo "${BOLD}==> Starting production stack with simulator${RESET}"
	@$(MAKE) docker-up-sim

test:
	@echo "${BOLD}==> Running backend tests (memory)${RESET}"
	@$(MAKE) backend-test

test-sqlite:
	@echo "${BOLD}==> Running backend tests (SQLite)${RESET}"
	@$(MAKE) backend-test-sqlite

stop:
	@echo "${BOLD}==> Stopping containers${RESET}"
	@docker compose -f infra/docker-compose.sqlite.yml --profile simulator down

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
	@echo "${BOLD}==> Starting containers (SQLite)${RESET}"
	@docker compose -f infra/docker-compose.sqlite.yml up -d --build

docker-down:
	@echo "${BOLD}==> Stopping containers (SQLite)${RESET}"
	@docker compose -f infra/docker-compose.sqlite.yml down

docker-up-sim:
	@echo "${BOLD}==> Starting containers + simulator (SQLite)${RESET}"
	@docker compose -f infra/docker-compose.sqlite.yml --profile simulator up -d --build

simulator-setup:
	@cp -n apps/simulator/.env.example apps/simulator/.env || true
	@cp -n apps/simulator/config.example.toml apps/simulator/config.toml || true
	@echo "${BOLD}==> Simulator config ready at apps/simulator/config.toml${RESET}"

simulator-up: simulator-setup
	@$(MAKE) docker-up-sim

simulator-down:
	@docker compose -f infra/docker-compose.sqlite.yml --profile simulator down
