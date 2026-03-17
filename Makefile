# --- Variáveis ---
COMPOSE_RUN := docker-compose

# --- Cores ---
BLUE   := \033[1;34m
GREEN  := \033[1;32m
RESET  := \033[0m

.PHONY: help build up down restart ingest chat logs status clean

help: ## Lista todos os comandos disponíveis
	@echo "$(BLUE)Comandos do Sistema RAG:$(RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(RESET) %s\n", $$1, $$2}'

up: ## Inicia os containers em background (Qdrant, Ollama, App)
	$(COMPOSE_RUN) up -d
	@echo "$(GREEN)Serviços iniciados! Use 'make status' para conferir.$(RESET)"

down: ## Para todos os serviços e remove os containers
	$(COMPOSE_RUN) down

restart: down up ## Reinicia todos os serviços

status: ## Exibe o estado dos containers
	$(COMPOSE_RUN) ps

logs: ## Mostra os logs em tempo real
	$(COMPOSE_RUN) logs -f

bash-ollama:
	$(COMPOSE_RUN) exec -it ollama bash

bash-sd:
	$(COMPOSE_RUN) exec -it stable-diffusion bash

bash-webui:
	$(COMPOSE_RUN) exec -it open-webui bash
	