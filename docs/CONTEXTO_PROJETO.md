# Contexto do Projeto CortAI - Estado Atual e Próximos Passos

## 📋 Visão Geral do Projeto

**CortAI** é uma plataforma de mídia inteligente que automatiza a análise, corte e publicação de vídeos de streams (YouTube, Twitch, etc.). O sistema utiliza análise multimodal (texto, áudio, imagem) para identificar momentos de destaque (highlights) e gerar clipes otimizados para redes sociais.

**Objetivo Principal:** Criar um pipeline robusto e escalável que transforma vídeos longos em clipes virais com mínima intervenção humana.

---

## 🏗️ Arquitetura Atual

### Stack Tecnológica

**Backend:**

- Python 3.11+ com FastAPI (Async)
- SQLAlchemy (ORM)
- Celery + Redis (Processamento assíncrono)
- LangGraph (Orquestração de agentes)
- OpenAI Whisper (Transcrição)
- Google Gemini (Análise multimodal)
- FFmpeg (Processamento de vídeo)
- PostgreSQL 16 (Banco de dados)

**Frontend:**

- React 19 + TypeScript
- Vite (Build tool)
- Tailwind CSS v4 (com plugin nativo Vite)
- Zustand (State management com devtools)
- React Router DOM (Roteamento)
- Lucide React (Ícones)

**Infraestrutura:**

- Docker Compose (configurado mas não testado)
- Redis 7 (Cache e filas)
- PostgreSQL 16

---

## ✅ O Que Já Foi Implementado

### 1. Frontend (100% Funcional)

- ✅ Setup completo com Tailwind CSS v4 (plugin nativo Vite)
- ✅ Design System: Componentes UI (Button, Input, Card, Badge)
- ✅ Layout principal com Sidebar e navegação
- ✅ Dashboard com input de URL e lista de vídeos
- ✅ Store Zustand configurada com devtools
- ✅ Integração com API (polling de status a cada 5s)
- ✅ Estrutura de pastas organizada (`components/ui`, `pages`, `store`, `lib`)

### 2. Backend - API REST (90% Funcional)

- ✅ FastAPI configurado com CORS
- ✅ Endpoint `POST /api/v1/videos/process` (inicia processamento)
- ✅ Endpoint `GET /api/v1/videos/status/{task_id}` (verifica status)
- ✅ Celery configurado (`backend/src/core/celery_app.py`)
- ✅ Task do Celery que executa o grafo LangGraph (`backend/src/core/tasks.py`)
- ✅ Estrutura de rotas organizada (`backend/src/api/routes/videos.py`)

### 3. Backend - Agentes de IA (100% Funcional)

- ✅ **Transcriber Agent** (`backend/src/agents/transcriber.py`):
  - Baixa vídeos do YouTube com `yt-dlp`
  - Transcreve áudio com OpenAI Whisper
  - Gera JSON com timestamps precisos
- ✅ **Analyst Agent** (`backend/src/agents/analyst.py`):
  - Analisa transcrições com Google Gemini
  - Identifica momentos de destaque
  - Retorna timestamps de início/fim em segundos
- ✅ **Editor Agent** (`backend/src/agents/editor.py`):
  - Corta vídeo com FFmpeg baseado nos timestamps
  - Gera arquivo final `highlight.mp4`

### 4. Backend - Orquestração (100% Funcional)

- ✅ Grafo LangGraph (`backend/src/core/graph.py`):
  - Nó 1: `node_transcrever` → Baixa e transcreve
  - Nó 2: `node_analisar` → Analisa e identifica highlights
  - Nó 3: `node_editar` → Corta o vídeo
  - Fluxo sequencial: transcrever → analisar → editar → END

---

## ⚠️ Problemas Conhecidos / Pendências

### 1. Erro de Importação do Gemini (RESOLVIDO)

- **Status:** ✅ Corrigido
- **Problema:** `AttributeError: module 'google.generativeai' has no attribute 'Client'`
- **Solução:** Atualizado para usar `genai.GenerativeModel()` e `genai.configure()`
- **Arquivo:** `backend/src/agents/analyst.py` (linhas 16, 181-184)

### 2. Configuração de Ambiente

- **Status:** ⚠️ Parcial
- **Arquivo `.env` necessário em `backend/.env`:**
  ```ini
  GOOGLE_API_KEY=sua_chave_aqui
  FFMPEG_PATH=ffmpeg
  REDIS_URL=redis://localhost:6379/0
  CELERY_BROKER_URL=redis://localhost:6379/1
  DATABASE_URL=postgresql://cortai:cortai_password@localhost:5432/cortai
  ```

### 3. Dependências Instaladas

- ✅ Celery, Redis, google-generativeai, langgraph, langchain
- ✅ FastAPI, uvicorn, pydantic
- ⚠️ Verificar se todas as dependências do `requirements.txt` estão instaladas

---

## 🚀 Próximos Passos Críticos

### Fase 1: Testes e Validação (PRIORIDADE ALTA)

1. **Testar Servidor Backend:**

   - Rodar `cd backend && uvicorn src.main:app --reload`
   - Verificar se inicia sem erros
   - Testar endpoint `/health`

2. **Testar Celery Worker:**

   - Rodar `cd backend && celery -A src.core.celery_app worker --loglevel=info`
   - Verificar conexão com Redis
   - Testar processamento de uma task

3. **Testar Integração Completa:**
   - Subir Frontend (`cd frontend && npm run dev`)
   - Subir Backend (uvicorn)
   - Subir Celery Worker
   - Subir Redis (`docker run -p 6379:6379 redis` ou via Docker Compose)
   - Testar fluxo completo: Frontend → API → Celery → Grafo → Agentes

### Fase 2: Melhorias e Robustez (PRIORIDADE MÉDIA)

1. **Tratamento de Erros:**

   - Adicionar try/except nos endpoints da API
   - Retornar mensagens de erro amigáveis
   - Logging estruturado

2. **Validação de URLs:**

   - Validar formato de URL do YouTube/Twitch antes de processar
   - Retornar erro 400 se URL inválida

3. **Progresso em Tempo Real:**

   - Atualizar status da task durante processamento (transcrevendo → analisando → editando)
   - Usar WebSocket ou Server-Sent Events para updates em tempo real (opcional)

4. **Persistência de Dados:**
   - Criar modelos SQLAlchemy para Video, Task, Clip
   - Salvar metadados no PostgreSQL
   - Implementar endpoints para listar vídeos processados

### Fase 3: Features Adicionais (PRIORIDADE BAIXA)

1. **Download de Clipes:**

   - Endpoint `GET /api/v1/clips/{clip_id}/download`
   - Servir arquivos de vídeo via FastAPI

2. **Thumbnails:**

   - Gerar thumbnails dos clipes
   - Endpoint para servir imagens

3. **Múltiplos Clipes:**

   - Modificar Analyst Agent para retornar múltiplos highlights
   - Processar vários cortes em paralelo

4. **Publisher Agent (Futuro):**
   - Publicar clipes automaticamente em redes sociais

---

## 📁 Estrutura de Arquivos Atual

```
CortAI/
├── backend/
│   ├── src/
│   │   ├── agents/
│   │   │   ├── transcriber.py ✅
│   │   │   ├── analyst.py ✅
│   │   │   └── editor.py ✅
│   │   ├── api/
│   │   │   └── routes/
│   │   │       └── videos.py ✅
│   │   ├── core/
│   │   │   ├── celery_app.py ✅
│   │   │   ├── tasks.py ✅
│   │   │   └── graph.py ✅
│   │   └── main.py ✅
│   ├── .env ⚠️ (precisa ser criado pelo usuário)
│   └── requirements.txt ✅
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/ ✅ (Button, Input, Card, Badge)
│   │   │   └── layout/ ✅ (AppLayout, Sidebar)
│   │   ├── pages/
│   │   │   └── Dashboard.tsx ✅
│   │   ├── store/
│   │   │   └── useVideoStore.ts ✅
│   │   └── App.tsx ✅
│   └── package.json ✅
├── graphs/ (legado - código movido para backend/src/core/graph.py)
├── agents/ (legado - código movido para backend/src/agents/)
└── docker-compose.yml ✅ (configurado mas não testado)
```

---

## 🔧 Comandos Úteis

### Backend

```bash
# Rodar servidor API
cd backend
uvicorn src.main:app --reload

# Rodar Celery Worker
cd backend
celery -A src.core.celery_app worker --loglevel=info

# Instalar dependências
pip install -r backend/requirements.txt
```

### Frontend

```bash
# Rodar servidor de desenvolvimento
cd frontend
npm run dev

# Build para produção
npm run build
```

### Infraestrutura

```bash
# Subir tudo com Docker Compose
docker-compose up -d

# Subir apenas Redis
docker run -p 6379:6379 redis
```

---

## 📝 Notas Importantes

1. **Arquivo `.env`:** Deve ser criado manualmente em `backend/.env` com as variáveis necessárias (não versionado no git).

2. **Redis:** É obrigatório para o Celery funcionar. Pode rodar via Docker ou instalação local.

3. **FFmpeg:** Deve estar no PATH do sistema ou configurado via `FFMPEG_PATH` no `.env`.

4. **Google API Key:** Obtida gratuitamente em https://aistudio.google.com/

5. **Estrutura Legada:** As pastas `agents/` e `graphs/` na raiz são legadas. O código ativo está em `backend/src/`.

---

## 🎯 Objetivo Imediato

**Fazer o sistema funcionar end-to-end:**

1. Frontend recebe URL → chama API
2. API cria task no Celery → retorna task_id
3. Celery Worker processa → executa grafo LangGraph
4. Agentes processam vídeo → geram highlight
5. Frontend atualiza status via polling → mostra resultado

**Status Atual:** Backend e Frontend prontos, falta testar integração completa.
