# --- Variáveis ---
COMPOSE_RUN := docker compose run

# --- Cores ---
BLUE   := \033[1;34m
GREEN  := \033[1;32m
RESET  := \033[0m

.PHONY: help build up down restart ingest chat logs status clean

help: ## Lista todos os comandos disponíveis
	@echo "$(BLUE)Comandos do Sistema RAG:$(RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(RESET) %s\n", $$1, $$2}'

up: ## Inicia os containers em background (Qdrant, Ollama, App)
	docker compose up -d
	@echo "$(GREEN)Serviços iniciados! Use 'make status' para conferir.$(RESET)"

down: ## Para todos os serviços e remove os containers
	docker compose down

restart: down up ## Reinicia todos os serviços

status: ## Exibe o estado dos containers
	docker compose ps

logs: ## Mostra os logs em tempo real
	docker compose logs -f

bash-ollama:
	docker compose exec -it ollama bash

bash-sd:
	docker compose exec -it stable-diffusion bash

bash-webui:
	docker compose exec -it open-webui bash
	