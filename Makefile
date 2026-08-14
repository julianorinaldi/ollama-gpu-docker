# --- Variáveis ---
# "docker-compose" (v1, do apt) está quebrado neste host — dá erro de
# "http+docker" ao falar com o daemon. O plugin v2 ("docker compose") é o que
# funciona, e é também o único que entende o docker-compose-sd.yml.
COMPOSE := docker compose
COMPOSE_SD := docker compose -f docker-compose-sd.yml
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

up: ## Inicia Ollama + Open WebUI (SEM geração de imagem)
	$(COMPOSE) up -d
	@echo "$(GREEN)Serviços iniciados! Use 'make status' para conferir.$(RESET)"

up-sd: ## Inicia a stack completa, com ComfyUI para gerar imagem
	$(COMPOSE_SD) up -d --build
	@echo "$(GREEN)ComfyUI em http://localhost:8188 | Open WebUI em http://localhost:3000$(RESET)"

down: ## Para todos os serviços e remove os containers
	$(COMPOSE_SD) down

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
	$(COMPOSE_EXEC) ollama bash

bash-sd:
	$(COMPOSE_SD) exec comfyui bash

bash-webui:
	$(COMPOSE_EXEC) open-webui bash
	