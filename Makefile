# --- Variáveis ---
COMPOSE := docker-compose
COMPOSE_EXEC := $(COMPOSE) exec
MODEL=mistral-nemo

# --- Cores ---
BLUE   := \033[1;34m
GREEN  := \033[1;32m
RESET  := \033[0m

.PHONY: help build up down restart ingest chat logs status clean

help: ## Lista todos os comandos disponíveis
	@echo "$(BLUE)Comandos do Sistema RAG:$(RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(RESET) %s\n", $$1, $$2}'

up: ## Inicia os containers em background (Qdrant, Ollama, App)
	$(COMPOSE) up -d
	@echo "$(GREEN)Serviços iniciados! Use 'make status' para conferir.$(RESET)"

down: ## Para todos os serviços e remove os containers
	$(COMPOSE) down

restart: down up ## Reinicia todos os serviços

status: ## Exibe o estado dos containers
	$(COMPOSE) ps

logs: ## Mostra os logs em tempo real
	$(COMPOSE) logs -f

## Lista os modelos instalados no server
list-llm:
	$(COMPOSE_EXEC) ollama ollama list

add-llm:
	$(COMPOSE_EXEC) ollama ollama run $(MODEL)

bash-ollama:
	$(COMPOSE_EXEC) -it ollama bash

bash-sd:
	$(COMPOSE_EXEC) -it stable-diffusion bash

bash-webui:
	$(COMPOSE_EXEC) -it open-webui bash
	