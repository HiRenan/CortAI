# Arquitetura do CortAI

## Visão Geral

O CortAI é uma plataforma de mídia inteligente que automatiza a análise, corte e publicação de vídeos de streams usando análise multimodal (texto, áudio e imagem).

## Componentes Principais

### 1. Backend (FastAPI)

#### Estrutura de Camadas

```
backend/src/
├── agents/          # Agentes de IA especializados
├── api/             # Endpoints REST
├── core/            # Lógica de negócio central
├── services/        # Integrações externas
├── models/          # Modelos de dados (ORM)
├── utils/           # Utilitários compartilhados
└── config/          # Configurações
```

#### Agentes de IA

1. **Transcriber Agent** (`agents/transcriber.py`)
   - Baixa vídeos do YouTube
   - Extrai e transcreve áudio usando Whisper
   - Gera arquivos de transcrição com timestamps

2. **Analyst Agent** (`agents/analyst.py`) [Em desenvolvimento]
   - Analisa transcrições para identificar momentos-chave
   - Usa modelos multimodais para análise de conteúdo
   - Detecta padrões de engajamento

3. **Editor Agent** (`agents/editor.py`) [Em desenvolvimento]
   - Corta vídeos baseado na análise
   - Gera múltiplas versões otimizadas
   - Adiciona legendas e thumbnails

4. **Publisher Agent** [Planejado]
   - Publica clipes nas redes sociais
   - Gerencia metadados e tags
   - Monitora performance

### 2. Frontend (React + Vite)

#### Estrutura de Componentes

```
frontend/src/
├── components/      # Componentes reutilizáveis
│   ├── common/     # Botões, inputs, etc
│   ├── video/      # Player, timeline, etc
│   ├── clips/      # Gerenciamento de clipes
│   └── dashboard/  # Painéis e gráficos
├── pages/          # Páginas da aplicação
├── services/       # Chamadas à API
├── hooks/          # Custom React Hooks
└── contexts/       # State management
```

### 3. Infraestrutura

#### Banco de Dados (PostgreSQL)
- Armazenamento de metadados de vídeos
- Informações de jobs e processamento
- Dados de usuários e autenticação

#### Cache & Queue (Redis)
- Cache de resultados frequentes
- Fila de processamento (Celery)
- Gerenciamento de jobs assíncronos

#### Storage
- Vídeos originais
- Clipes gerados
- Thumbnails
- Arquivos temporários

## Fluxo de Dados

```
1. Usuário submete URL → Frontend
2. Frontend → Backend API → Cria Job
3. Celery Worker pega o job
4. Transcriber Agent → Baixa e transcreve
5. Analyst Agent → Analisa e identifica cortes
6. Editor Agent → Gera clipes
7. Resultados → Salvos no Storage
8. Notificação → Frontend via WebSocket
9. Usuário visualiza clipes gerados
```

## Tecnologias

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **ORM**: SQLAlchemy
- **Tasks**: Celery
- **IA**: OpenAI Whisper, Transformers

### Frontend
- **Framework**: React 18
- **Build**: Vite
- **State**: Zustand
- **UI**: Tailwind CSS

### Infraestrutura
- **Database**: PostgreSQL 16
- **Cache**: Redis 7
- **Container**: Docker + Docker Compose

## Escalabilidade

### Processamento Assíncrono
- Jobs pesados executados em workers Celery
- Múltiplos workers podem processar simultaneamente
- Retry automático em caso de falha

### Cache Inteligente
- Transcrições cacheadas
- Análises reutilizáveis
- Redução de processamento redundante

### Storage Distribuído
- Possibilidade de usar S3/MinIO
- CDN para servir clipes
- Cleanup automático de arquivos antigos

## Segurança

- Autenticação JWT
- CORS configurável
- Validação de inputs com Pydantic
- Rate limiting
- Sanitização de dados

## Monitoramento

- Logs estruturados
- Health checks
- Métricas de performance
- Tracking de jobs
