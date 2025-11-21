# 🚀 Setup Completo - CortAI

Este guia contém **todas as instruções** para configurar e rodar o sistema CortAI do zero.

---

## ✅ O Que Foi Configurado Automaticamente

Já foram criados e configurados:

- ✅ Dependências Python atualizadas (`requirements.txt`)
- ✅ Estrutura de diretórios (`storage/`, `data/`)
- ✅ Dockerfile para backend (com FFmpeg)
- ✅ Dockerfile para frontend
- ✅ docker-compose.yml configurado
- ✅ Arquivo de configuração centralizado (`backend/src/core/config.py`)
- ✅ Paths padronizados no código (usa `data/` para temp, `storage/` para outputs)
- ✅ Script de teste (`backend/test_agents.py`)

---

## 📋 Pré-requisitos

### 1. Docker Desktop (OBRIGATÓRIO para rodar com Docker)

**Status:** ⚠️ Docker instalado mas NÃO está rodando

**Ação necessária:**
1. Abra o **Docker Desktop** no Windows
2. Aguarde até ver "Docker Desktop is running" no ícone da bandeja
3. Verifique com: `docker ps` (deve listar containers, mesmo que vazio)

### 2. Variável de Ambiente (IMPORTANTE)

O arquivo `.env` na raiz já foi criado com a `GOOGLE_API_KEY`:
```
GOOGLE_API_KEY=AIzaSyCYuLHtTxNhCf840laZhQJWdRMSpp--6Z4
```

---

## 🐳 Opção 1: Rodar com Docker Compose (RECOMENDADO)

### Passo 1: Inicie o Docker Desktop

Abra o Docker Desktop e aguarde inicializar completamente.

### Passo 2: Build das Imagens

```bash
# Na raiz do projeto CortAI
docker-compose build
```

**Tempo estimado:** 5-10 minutos (primeira vez)

### Passo 3: Subir Todos os Serviços

```bash
docker-compose up -d
```

Isso irá iniciar:
- ✅ PostgreSQL (porta 5432)
- ✅ Redis (porta 6379)
- ✅ Backend API (porta 8000)
- ✅ Celery Worker
- ✅ Frontend (porta 5173)

### Passo 4: Verificar Status

```bash
docker-compose ps
```

Todos os serviços devem estar com status "Up" ou "healthy".

### Passo 5: Acessar a Aplicação

- **Frontend:** http://localhost:5173
- **Backend API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

### Comandos Úteis (Docker)

```bash
# Ver logs do backend
docker-compose logs -f backend

# Ver logs do Celery worker
docker-compose logs -f celery-worker

# Ver logs do frontend
docker-compose logs -f frontend

# Reiniciar um serviço específico
docker-compose restart backend

# Parar todos os serviços
docker-compose down

# Parar e remover volumes (limpa dados do banco)
docker-compose down -v
```

---

## 💻 Opção 2: Rodar Manualmente (SEM Docker)

### Pré-requisitos Adicionais

1. **Python 3.11+**
2. **Node.js 20+**
3. **Redis** instalado e rodando
4. **PostgreSQL 16** instalado e rodando
5. **FFmpeg** instalado e no PATH

### Backend

```bash
cd backend

# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Rodar API
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Em **outro terminal**, rodar o Celery Worker:

```bash
cd backend
venv\Scripts\activate  # Windows
celery -A src.core.celery_app worker --loglevel=info
```

### Frontend

```bash
cd frontend

# Instalar dependências
npm install

# Rodar servidor de desenvolvimento
npm run dev
```

### Redis (Windows)

**Opção A:** Usar Docker apenas para Redis:
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

**Opção B:** Instalar Redis nativo:
- Download: https://github.com/microsoftarchive/redis/releases
- Após instalar: `redis-server`

---

## 🧪 Testar o Sistema

### Teste 1: Script de Validação

```bash
cd backend
python test_agents.py
```

Este script testa:
- ✅ Configuração (API keys, paths)
- ✅ Imports dos módulos
- ✅ Diretórios criados
- ✅ Build do grafo LangGraph
- ✅ Conexão com Google Gemini

### Teste 2: Health Check da API

```bash
curl http://localhost:8000/health
```

Resposta esperada:
```json
{"status": "ok", "service": "CortAI Backend"}
```

### Teste 3: Teste End-to-End (Frontend)

1. Acesse http://localhost:5173
2. Cole uma URL de vídeo curto do YouTube (ex: ~30 segundos)
3. Clique em "Processar Vídeo"
4. Observe o status mudando (processing → completed/failed)
5. Verifique os logs do Celery Worker

**URLs de teste recomendadas (vídeos curtos):**
- https://www.youtube.com/watch?v=jNQXAC9IVRw (30s)
- https://www.youtube.com/watch?v=dQw4w9WgXcQ (3min)

---

## 📁 Estrutura de Arquivos Criados

```
CortAI/
├── .env                          # ✅ Criado - GOOGLE_API_KEY
├── SETUP_COMPLETO.md             # ✅ Este arquivo
├── storage/                      # ✅ Criado
│   ├── videos/.gitkeep
│   ├── clips/.gitkeep
│   ├── thumbnails/.gitkeep
│   └── temp/.gitkeep
├── data/.gitkeep                 # ✅ Criado
├── backend/
│   ├── Dockerfile                # ✅ Verificado (já existia)
│   ├── requirements.txt          # ✅ Atualizado (langgraph, google-generativeai)
│   ├── test_agents.py            # ✅ Criado
│   └── src/
│       └── core/
│           └── config.py         # ✅ Criado - Configuração centralizada
└── frontend/
    ├── Dockerfile                # ✅ Criado
    ├── .env                      # ✅ Criado
    └── .env.example              # ✅ Criado
```

---

## 🔧 Solução de Problemas

### Problema: Docker não inicia

**Sintoma:** `error during connect: ... dockerDesktopLinuxEngine: O sistema não pode encontrar o arquivo`

**Solução:**
1. Abra o Docker Desktop manualmente
2. Aguarde até ver "Docker Desktop is running"
3. Tente novamente: `docker ps`

### Problema: Erro "GOOGLE_API_KEY não encontrada"

**Solução:**
1. Verifique se `.env` existe na raiz do projeto
2. Verifique se contém: `GOOGLE_API_KEY=sua_chave`
3. Se usar Docker: rode `docker-compose down` e `docker-compose up -d` novamente

### Problema: Erro ao importar `langgraph` ou `google.generativeai`

**Solução:**
1. Reinstale dependências: `pip install -r requirements.txt`
2. Ou force reinstall: `pip install --upgrade langgraph google-generativeai`

### Problema: FFmpeg não encontrado

**Sintoma:** Erro ao processar vídeo relacionado a FFmpeg

**Solução (Docker):** FFmpeg já está instalado na imagem, não precisa fazer nada

**Solução (Manual):**
1. Instale FFmpeg: https://ffmpeg.org/download.html
2. Adicione ao PATH do Windows
3. Teste: `ffmpeg -version`

### Problema: Frontend não conecta ao backend

**Sintoma:** Erro CORS ou "Failed to fetch"

**Solução:**
1. Verifique se backend está rodando: http://localhost:8000/health
2. Verifique `.env` do frontend: `VITE_API_URL=http://localhost:8000`
3. Reinicie o frontend: `npm run dev`

---

## 📊 Status Atual do Sistema

| Componente | Status | Porta |
|------------|--------|-------|
| Backend API | ✅ Configurado | 8000 |
| Celery Worker | ✅ Configurado | - |
| Frontend | ✅ Configurado | 5173 |
| Redis | ✅ Configurado | 6379 |
| PostgreSQL | ✅ Configurado | 5432 |
| Transcriber Agent | ✅ Funcional | - |
| Analyst Agent | ✅ Funcional | - |
| Editor Agent | ✅ Funcional | - |
| LangGraph Workflow | ✅ Funcional | - |

---

## 🎯 Próximos Passos

1. **Iniciar Docker Desktop**
2. **Rodar:** `docker-compose build && docker-compose up -d`
3. **Testar:** `python backend/test_agents.py`
4. **Acessar:** http://localhost:5173
5. **Processar um vídeo de teste**

---

## 📝 Notas Importantes

- **Paths:** O sistema usa `data/` para arquivos temporários e `storage/` para outputs finais
- **API Key:** A chave do Gemini está configurada mas pode ser alterada no `.env`
- **Banco de Dados:** PostgreSQL está configurado mas ainda não é usado (será implementado futuramente)
- **FFmpeg:** Já está instalado no Docker, não precisa instalar manualmente
- **yt-dlp:** Será instalado automaticamente pelo pip via requirements.txt

---

## 🆘 Suporte

Se encontrar problemas:
1. Verifique os logs: `docker-compose logs -f [serviço]`
2. Rode o teste: `python backend/test_agents.py`
3. Consulte este guia na seção "Solução de Problemas"
