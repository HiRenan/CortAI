# CortAI 🎬

**Agente de Mídia Inteligente**: Geração de Múltiplos Cortes de Mídia em Tempo Real com Inteligência Multimodal

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://reactjs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 Visão Geral

CortAI é uma plataforma projetada para **automatizar a análise, corte e publicação de vídeos** provenientes de streams (YouTube, Twitch, podcasts e eventos ao vivo). Utilizando **análise multimodal** (texto, áudio e imagem), o sistema identifica automaticamente momentos de destaque, gerando clipes curtos com legendas e miniaturas prontos para redes sociais.

## ✨ Funcionalidades

- 🎥 **Download automático** de vídeos do YouTube, Twitch e outras plataformas
- 🎤 **Transcrição de áudio** usando OpenAI Whisper com timestamps precisos
- 🧠 **Análise multimodal** para identificar momentos-chave e highlights
- ✂️ **Corte inteligente** de vídeos baseado em análise de conteúdo
- 📱 **Otimização automática** para diferentes formatos e redes sociais
- 🖼️ **Geração de thumbnails** e legendas automatizadas
- 📊 **Dashboard** para gerenciar vídeos e clipes
- ⚡ **Processamento assíncrono** com filas para alta performance

## 🏗️ Estrutura do Projeto

```
CortAI/
├── backend/          # API FastAPI + Celery + LangGraph + agentes (transcriber, analyst, editor)
├── frontend/         # UI React + Vite + Tailwind + Zustand
├── infra/            # Configurações de infraestrutura
├── storage/          # Armazenamento de mídia (gitignored)
├── data/             # Artefatos intermediários (gitignored; montado no container)
├── docs/             # Documentação
└── docker-compose.yml
```

### Stack Tecnológica

**Backend**
- FastAPI (Python 3.11)
- PostgreSQL (metadados)
- Redis + Celery (tasks async)
- LangGraph (orquestração)
- Whisper (transcrição)
- Gemini (análise) – exige `GOOGLE_API_KEY`
- FFmpeg (corte)

**Frontend**
- React 18, Vite, Tailwind, Zustand

**Infra**
- Docker & Docker Compose

## 🚀 Quick Start (Docker)

```bash
# Clone
git clone <repository-url>
cd CortAI

# Configurar .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
# preencha GOOGLE_API_KEY e ajuste DATABASE_URL/REDIS_URL/FFMPEG_PATH se necessário

# Subir serviços
docker-compose up -d --build

# Rodar migrações (obrigatório)
docker-compose run --rm backend alembic upgrade head

# Acessos
# Frontend: http://localhost:5173
# Backend:  http://localhost:8000
# Swagger:  http://localhost:8000/docs
```

Instalação manual em [docs/SETUP.md](docs/SETUP.md).

## 📚 Documentação

- [Guia de Configuração](docs/SETUP.md)
- [Arquitetura](docs/ARCHITECTURE.md)
- [Swagger](http://localhost:8000/docs) – API real
- [Agents README](backend/src/agents/README.md)

## 🤖 Agentes

- Transcriber: download + Whisper
- Analyst: highlights (Gemini, RAG)
- Editor: corte FFmpeg, SRT/VTT/thumbnail
- Publisher: planejado

## 🛠️ Desenvolvimento

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn src.main:app --reload

# Frontend
cd frontend
npm install
npm run dev

# Testes
pytest
npm test
```

## 📊 Status

| Componente       | Status                  |
|------------------|-------------------------|
| Transcriber      | ✅ Em uso               |
| Analyst          | ✅ Em uso (Gemini)      |
| Editor           | ✅ Em uso               |
| Backend API      | ✅ Em uso (/videos)     |
| Frontend         | ✅ Dashboard/Biblioteca |
| Docker Setup     | ✅ Configurado          |

## 📄 Licença

MIT. Veja [LICENSE](LICENSE).

## 👥 Autores

Equipe CortAI

---

Para mais informações, consulte a [documentação completa](docs/).
