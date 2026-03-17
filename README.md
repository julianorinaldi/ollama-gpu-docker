Ollama + Stable Diffusion + Open WebUI com GPU
=============================================

Este projeto fornece um ambiente Docker pronto para uso com:

- **Ollama** – servidor de modelos de linguagem (LLMs) com suporte a GPU.
- **Stable Diffusion (AI-Dock WebUI)** – geração de imagens com GPU.
- **Open WebUI** – interface web unificada para conversar com LLMs e, opcionalmente, integrar geração de imagens.

Tudo é orquestrado via `docker-compose` e um `Makefile` simples para facilitar o dia a dia.

---

## Requisitos

- **Docker** instalado e funcionando.
- **Docker Compose** (ou `docker compose` integrado ao Docker).
- **GPU NVIDIA** com drivers corretos instalados.
- **NVIDIA Container Toolkit** configurado (para que os containers tenham acesso à GPU).
- Opcional: arquivo `.env` na raiz do projeto com variáveis de ambiente que você quiser passar para `ollama` e `open-webui`.

---

## Estrutura dos serviços (docker-compose)

Arquivo: `docker-compose.yml`

### Serviço `ollama`

- **Imagem**: `ollama/ollama:latest`
- **Porta exposta**: `11434:11434`
- **Volume**: `./volumes/ollama:/root/.ollama`
  - Garante persistência dos modelos baixados e cache.
- **GPU**:
  - Reserva **todas** as GPUs NVIDIA disponíveis (`driver: nvidia`, `count: all`, `capabilities: [gpu]`).
- **Env file**:
  - Lê variáveis de `.env` (por exemplo, proxies, chaves, etc.).
- **Propósito**:
  - Servir modelos de linguagem via API (HTTP) com aceleração por GPU.

### Serviço `stable-diffusion`

- **Imagem**: `ghcr.io/ai-dock/stable-diffusion-webui:latest-cuda`
- **Portas expostas**:
  - `7860:7860` – interface web principal / proxy.
  - `17860:17860` – possível porta de API direta.
  - `8888:8888` – geralmente Jupyter/config nas imagens AI-Dock.
- **Variáveis de ambiente principais**:
  - `WEBUI_ARGS=--api --listen --xformers`
    - `--api`: habilita a API HTTP.
    - `--listen`: escuta em `0.0.0.0` (acessível de fora do container).
    - `--xformers`: ativa otimizações para GPU.
  - `AUTH_ENABLE=false`
    - Desativa autenticação (adequado para uso em rede local / ambiente controlado).
- **Volume**:
  - `./volumes/sd-data:/workspace`
  - Persiste modelos, configurações e imagens geradas.
- **GPU**:
  - Usa GPUs NVIDIA com as mesmas reservas que o serviço `ollama`.
- **Propósito**:
  - Interface e API de Stable Diffusion para geração de imagens usando GPU.

### Serviço `open-webui`

- **Imagem**: `ghcr.io/open-webui/open-webui:main`
- **Porta exposta**: `3000:8080`
  - Acesse em `http://localhost:3000`.
- **Volume**:
  - `./volumes/open-webui:/app/backend/data`
  - Persiste dados da aplicação: histórico, configurações, etc.
- **Env file**:
  - Também lê variáveis de `.env`.
- **depends_on**:
  - `ollama`
  - `stable-diffusion`
  - Garante que os backends de texto e imagem estejam disponíveis para a interface.
- **Propósito**:
  - Interface web amigável para interagir com o Ollama (LLMs) e, opcionalmente, com Stable Diffusion.

---

## Makefile: comandos disponíveis

Arquivo: `Makefile`

Principais alvos:

- **`make help`**  
  Lista todos os comandos disponíveis com uma breve descrição.

- **`make up`**  
  - Sobe todos os serviços definidos em `docker-compose.yml` em **background**.
  - Após executar, você pode:
    - Acessar o **Open WebUI** em `http://localhost:3000`.
    - Acessar a interface do **Stable Diffusion WebUI** (normalmente em `http://localhost:7860`).
    - Consumir a **API do Ollama** em `http://localhost:11434`.

- **`make down`**  
  - Para todos os serviços e **remove os containers** criados pelo `docker compose up`.

- **`make restart`**  
  - Equivalente a `make down` seguido de `make up`.
  - Útil para aplicar mudanças rápidas na configuração.

- **`make status`**  
  - Executa `docker compose ps` e mostra o estado atual dos containers (up, exited, ports, etc.).

- **`make logs`**  
  - Mostra os logs de todos os serviços em tempo real (`docker compose logs -f`).

- **`make bash-ollama`**  
  - Abre um shell bash **dentro do container** `ollama`.

- **`make bash-sd`**  
  - Abre um shell bash **dentro do container** `stable-diffusion`.

- **`make bash-webui`**  
  - Abre um shell bash **dentro do container** `open-webui`.

---

## Passo a passo para usar o projeto

1. **Clonar o repositório**

   ```bash
   git clone <URL-DO-REPOSITORIO>
   cd ollama-gpu-docker
   ```

2. **Criar o arquivo `.env` (opcional, mas recomendado)**

   - Crie um arquivo `.env` na raiz se precisar adicionar variáveis como:
     - Proxies
     - Chaves de API
     - Configurações específicas da Open WebUI ou do Ollama
   - Exemplo simples (apenas ilustrativo):

   ```bash
   # .env
   # OPENWEBUI_SECRET_KEY=algum_valor
   # OLLAMA_HOST=0.0.0.0
   ```

3. **Subir os serviços**

   Usando o Makefile:

   ```bash
   make up
   ```

   Ou diretamente com Docker Compose:

   ```bash
   docker compose up -d
   ```

4. **Verificar status**

   ```bash
   make status
   ```

5. **Acessar as interfaces**

- **Open WebUI (LLMs)**:  
  `http://localhost:3000`

- **Stable Diffusion WebUI (imagens)**:  
  `http://localhost:7860`

- **API do Ollama (LLMs)**:  
  `http://localhost:11434`

6. **Ver logs**

   ```bash
   make logs
   ```

7. **Entrar nos containers (debug/avançado)**

   - Ollama:

     ```bash
     make bash-ollama
     ```

   - Stable Diffusion:

     ```bash
     make bash-sd
     ```

   - Open WebUI:

     ```bash
     make bash-webui
     ```

8. **Parar tudo**

   ```bash
   make down
   ```

---

## Notas e boas práticas

- **Persistência de dados**  
  Certifique-se de que a pasta `./volumes` esteja versionada/ignoranda conforme sua preferência:
  - Em geral, é uma boa ideia manter `volumes` no `.gitignore`, pois conterá modelos pesados e dados gerados.

- **Segurança**  
  - O `AUTH_ENABLE=false` no `stable-diffusion` significa que **não há autenticação** na interface.  
  - Não exponha as portas do projeto diretamente para a internet sem antes proteger (proxy reverso com autenticação, VPN, etc.).

- **Uso de GPU em múltiplos serviços**  
  - Tanto `ollama` quanto `stable-diffusion` usam `count: all` para GPUs NVIDIA.  
  - Em ambientes com várias GPUs, avalie se vale limitar cada serviço a GPUs específicas.

---

## Resumo rápido

- **Subir tudo**: `make up`
- **Ver status**: `make status`
- **Ver logs**: `make logs`
- **Parar tudo**: `make down`
- **Open WebUI**: `http://localhost:3000`
- **Stable Diffusion WebUI**: `http://localhost:7860`
- **API Ollama**: `http://localhost:11434`

---

## Usar o Ollama a partir de outro PC na rede (LAN)

Se você já consegue abrir o Open WebUI em `http://192.168.100.105:3000`, o próximo passo é expor e testar **a API do Ollama** na mesma máquina.

### 1) Garantir que o Ollama está escutando na rede

Este repositório aplica o `.env` também no container `ollama`. Como o `.env` costuma definir `OLLAMA_HOST` para o **Open WebUI** (ex.: `http://ollama:11434`), o `docker-compose` faz override no serviço `ollama` para:

- `OLLAMA_HOST=0.0.0.0:11434`

Após alterar/atualizar, reinicie:

```bash
make restart
```

### 2) Testar do outro PC (recomendado: `curl`)

No **outro PC** (cliente), rode:

1) Ver modelos disponíveis (se der resposta, a rede está OK):

```bash
curl -s "http://192.168.100.105:11434/api/tags"
```

2) Fazer uma geração simples (streaming):

```bash
curl -N "http://192.168.100.105:11434/api/generate" \
  -H "Content-Type: application/json" \
  -d '{"model":"mistral-nemo","prompt":"Responda em uma frase: o que é o Ollama?"}'
```

Se o modelo ainda não estiver baixado, você pode baixar pelo servidor (na máquina do Ollama):

```bash
make add-llm
```

### 3) Se não responder: liberar a porta no firewall

Na **máquina do servidor** (192.168.100.105), se você usa UFW:

```bash
sudo ufw allow 11434/tcp
sudo ufw status
```

### 4) Configurar um app/cliente para usar o Ollama remoto

- **Endpoint**: `http://192.168.100.105:11434`
- **Modelos**: use o nome que aparecer no `/api/tags` (ex.: `mistral-nemo`)

Dica: o Open WebUI já usa o backend `ollama` via rede interna do Docker. Para consumir de fora (outro PC), sempre use o IP da máquina + porta `11434`.

Com isso, qualquer pessoa consegue entender rapidamente o propósito dos containers, como subir o ambiente e onde acessar cada serviço.