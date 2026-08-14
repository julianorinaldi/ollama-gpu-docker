Ollama + ComfyUI + Open WebUI com GPU
=====================================

Este projeto fornece um ambiente Docker pronto para uso com:

- **Ollama** – servidor de modelos de linguagem (LLMs) com suporte a GPU.
- **ComfyUI** – geração de imagens com GPU, com interface e API HTTP.
- **Open WebUI** – interface web unificada para conversar com LLMs e gerar imagens.

Tudo é orquestrado via `docker compose` e um `Makefile` simples para facilitar o dia a dia.

> **Atenção aos dois arquivos de compose.** O `docker-compose.yml` (padrão) sobe
> **só** Ollama + Open WebUI, **sem** geração de imagem. Quem tem imagem é o
> `docker-compose-sd.yml` — use `make up-sd`.

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

### Serviço `comfyui`

- **Imagem**: build local (`docker/Dockerfile.comfyui`), a partir de
  `pytorch/pytorch:2.9.1-cuda12.8-cudnn9-runtime`.
- **Porta exposta**: `8188:8188` – interface web e API HTTP (`/prompt`).
- **Volumes**:
  - `./models/checkpoints` → os `.safetensors`. Fica **fora** de `volumes/`
    porque `volumes/` pertence ao root e este diretório precisa ser gravável
    pelo usuário que baixa os modelos.
  - `./saida` → imagens geradas.
- **GPU**: mesmas reservas do serviço `ollama`.

Substituiu o antigo `ghcr.io/ai-dock/stable-diffusion-webui` (AUTOMATIC1111),
que nunca chegou a subir aqui — `volumes/sd-data` jamais foi criado. O ComfyUI
é o que segue mantido, roda SDXL folgado em 12 GB e tem API HTTP própria, o que
permite gerar em lote por script sem passar pela interface.

**Não use uma base de torch antiga** neste Dockerfile: o `comfy_kitchen` do
ComfyUI registra um custom op com assinatura `list[int]`, que o `infer_schema`
do torch 2.5 rejeita. O container sobe, estoura no import e nunca abre a 8188.

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
  - Sobe apenas Ollama + Open WebUI (`docker-compose.yml`), **sem** geração de imagem.

- **`make up-sd`**  
  - Sobe a stack completa (`docker-compose-sd.yml`), construindo o ComfyUI se preciso.
  - Após executar, você pode:
    - Acessar o **Open WebUI** em `http://localhost:3000`.
    - Acessar o **ComfyUI** em `http://localhost:8188`.
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
  - Abre um shell bash **dentro do container** `comfyui`.

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

- **Subir tudo (com imagem)**: `make up-sd`
- **Ver status**: `make status`
- **Ver logs**: `make logs`
- **Parar tudo**: `make down`
- **Open WebUI**: `http://localhost:3000`
- **ComfyUI**: `http://localhost:8188`
- **API Ollama**: `http://localhost:11434`

---

## Modelos de imagem

Os checkpoints **não** são versionados (`models/` está no `.gitignore`). Baixe
o que for usar para `models/checkpoints/`:

```bash
cd models/checkpoints
curl -L -O https://huggingface.co/cagliostrolab/animagine-xl-4.0/resolve/main/animagine-xl-4.0-opt.safetensors
```

Comparação feita em 14/08/2026 numa RTX 3060 12 GB, gerando cartas de
personagem para o jujutsu-kaisen.com — mesmo prompt, mesma seed:

| modelo | tamanho | veredito |
|---|---|---|
| **Animagine XL 4.0** | 6,5 GB | **Escolhido.** Arte limpa, respeita a paleta pedida, não inventa moldura nem texto. |
| NoobAI-XL v1.1 | 6,6 GB | Composição mais dramática, mas desenha moldura de carta, texto embolado e marca d'água falsa. Atrapalha aqui, porque a moldura da carta é do CSS. |
| SDXL base 1.0 | 6,6 GB | Não conhece os personagens. Serve para cenário, não para personagem. |

O que faz esses modelos valerem a pena não é a qualidade geral: é o
**vocabulário Danbooru**. `gojou satoru` não é descrição, é um identificador que
o modelo aprendeu — devolve o personagem certo, com a venda certa. Escrever
"Satoru Gojo" em inglês corrente devolve um sujeito genérico de cabelo branco.
Por isso os scripts em `scripts/` carregam um mapa de tags separado: o JSON do
site guarda o nome de exibição em pt-BR, que não serve como prompt.

Duas armadilhas que custaram uma leva inteira:

- **Ausência se pede no negativo.** "sem brilho" no prompt positivo produziu
  exatamente brilho — o modelo lê a palavra e desenha. Para a Restrição
  Celestial (Toji, Maki) o "no glow" precisa estar no `negative_prompt`.
- **O CLIP corta em 77 tokens.** Como as tags de qualidade ficam no fim do
  prompt, são elas que se perdem. Prompt curto não é estilo, é requisito.

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