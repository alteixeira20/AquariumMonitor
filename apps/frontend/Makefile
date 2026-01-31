# AquariumMonitor frontend

GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
RESET := \033[0m
BOLD := \033[1m

.PHONY: help deps dev build start lint test clean

help:
	@echo "${BOLD}AquariumMonitor frontend${RESET}"
	@echo ""
	@echo "${BOLD}Most used${RESET}"
	@echo "  ${GREEN}make dev${RESET}     Run Next.js dev server"
	@echo "  ${GREEN}make build${RESET}   Build production assets"
	@echo "  ${GREEN}make start${RESET}   Start production server"
	@echo "  ${GREEN}make lint${RESET}    Lint frontend"
	@echo "  ${GREEN}make test${RESET}    Run frontend checks"

node_modules:
	@npm install


deps: node_modules


dev: deps
	@echo "${BOLD}==> Starting Next.js dev server${RESET}"
	@NODE_PATH=$(CURDIR)/node_modules npm run dev

build: deps
	@echo "${BOLD}==> Building frontend${RESET}"
	@NODE_PATH=$(CURDIR)/node_modules npm run build

start:
	@echo "${BOLD}==> Starting frontend${RESET}"
	@NODE_PATH=$(CURDIR)/node_modules npm run start

lint: deps
	@echo "${BOLD}==> Linting frontend${RESET}"
	@NODE_PATH=$(CURDIR)/node_modules npm run lint

test: lint

clean:
	@rm -rf node_modules .next
	@echo "${BOLD}==> Removed node_modules and .next${RESET}"
