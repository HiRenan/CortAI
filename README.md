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

## 🏗️ Arquitetura

```
CortAI/
├── backend/          # API FastAPI + Agentes de IA
├── frontend/         # Interface React + Vite
├── shared/           # Tipos e schemas compartilhados
├── infra/            # Configurações de infraestrutura
├── storage/          # Armazenamento de mídia (git ignored)
├── docs/             # Documentação completa
└── scripts/          # Scripts utilitários
```

### Stack Tecnológica

**Backend:**
- FastAPI (Python) - API REST moderna e async
- PostgreSQL - Banco de dados relacional
- Redis - Cache e filas de processamento
- Celery - Processamento de tarefas assíncronas
- OpenAI Whisper - Transcrição de áudio
- FFmpeg - Processamento de vídeo

**Frontend:**
- React 18 - Framework UI
- Vite - Build tool ultra-rápido
- Tailwind CSS - Estilização
- Zustand - Gerenciamento de estado

**Infraestrutura:**
- Docker & Docker Compose - Containerização
- Nginx - Proxy reverso (produção)

## 🚀 Quick Start

### Usando Docker (Recomendado)

```bash
# Clone o repositório
git clone <repository-url>
cd CortAI

# Configure as variáveis de ambiente
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Inicie todos os serviços
docker-compose up -d

# Acesse a aplicação
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Instalação Manual

Veja o guia completo em [docs/SETUP.md](docs/SETUP.md)

## 📚 Documentação

- [Guia de Configuração](docs/SETUP.md) - Instruções detalhadas de instalação
- [Arquitetura](docs/ARCHITECTURE.md) - Visão técnica da arquitetura
- [API Documentation](http://localhost:8000/docs) - Swagger UI interativo
- [Agents README](backend/src/agents/README.md) - Documentação dos agentes de IA

## 🤖 Agentes Inteligentes

### 1. Transcriber Agent ✅
Baixa vídeos e transcreve áudio usando Whisper

### 2. Analyst Agent 🚧
Analisa conteúdo e identifica momentos de destaque

### 3. Editor Agent 🚧
Gera clipes otimizados automaticamente

### 4. Publisher Agent 📋
Publica clipes nas redes sociais (planejado)

## 🛠️ Desenvolvimento

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn src.main:app --reload

# Frontend
cd frontend
npm install
npm run dev

# Testes
pytest                    # Backend
npm test                  # Frontend
```

## 📊 Status do Projeto

| Componente | Status |
|------------|--------|
| Transcriber Agent | ✅ Implementado |
| Analyst Agent | 🚧 Em desenvolvimento |
| Editor Agent | 🚧 Em desenvolvimento |
| Backend API | 🚧 Em desenvolvimento |
| Frontend | 🚧 Em desenvolvimento |
| Docker Setup | ✅ Configurado |

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor, leia o guia de contribuição antes de submeter PRs.

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 👥 Autores

Desenvolvido com ❤️ pela equipe CortAI

---

Para mais informações, consulte a [documentação completa](docs/).