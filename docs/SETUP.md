# Guia de Configuração - CortAI

## Pré-requisitos

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose
- FFmpeg instalado ou caminho configurado via `FFMPEG_PATH`
- Conta Google Gemini (`GOOGLE_API_KEY`)
- Git

## Instalação

### 1. Clone o Repositório

```bash
git clone <repository-url>
cd CortAI
```

### 2. Configuração com Docker (Recomendado)

```bash
# Subir serviços
docker-compose up -d --build

# Rodar migrações (obrigatório)
docker-compose run --rm backend alembic upgrade head

# Ver logs
docker-compose logs -f

# Parar
docker-compose down
```

Serviços:
- Backend API: http://localhost:8000
- Frontend: http://localhost:5173
- PostgreSQL: localhost:5432
- Redis: localhost:6379

### 3. Configuração Manual (sem Docker)

#### Backend

```bash
cd backend

# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
cp .env.example .env
# Edite o .env com suas configurações (DB, Redis, GOOGLE_API_KEY, FFMPEG_PATH)

# Executar migrações
alembic upgrade head

# Iniciar servidor
uvicorn src.main:app --reload
```

#### Frontend

```bash
cd frontend

# Instalar dependências
npm install

# Configurar variáveis de ambiente
cp .env.example .env
VITE_API_URL=http://localhost:8000

# Iniciar servidor de desenvolvimento
npm run dev
```

#### Celery Worker

```bash
cd backend
source venv/bin/activate
celery -A src.core.celery_app worker --loglevel=info
```

## Configuração do FFmpeg

### Linux (Ubuntu/Debian)

```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

### macOS

```bash
brew install ffmpeg
```

### Windows

1. Baixe o FFmpeg de https://ffmpeg.org/download.html
2. Extraia para um diretório (ex: `C:\ffmpeg`)
3. Adicione o caminho ao PATH ou configure no `.env`:
   ```
   FFMPEG_PATH=C:\ffmpeg\bin\ffmpeg.exe
   ```

## Configuração do Banco de Dados

### PostgreSQL Local

```bash
# Criar banco de dados
createdb cortai

# Ou via psql
psql -U postgres
CREATE DATABASE cortai;
```

### Redis Local

```bash
# Linux
sudo apt-get install redis-server
redis-server

# macOS
brew install redis
brew services start redis
```

## Variáveis de Ambiente

### Backend (.env)

```env
# Application
APP_NAME=CortAI
APP_ENV=development
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DATABASE_URL=postgresql+asyncpg://cortai:cortai_password@localhost:5432/cortai

# Redis / Celery
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1

# RabbitMQ (opcional para pipeline legacy)
RABBITMQ_URL=amqp://cortai:cortai_password@localhost:5672/

# FFmpeg
FFMPEG_PATH=/usr/bin/ffmpeg  # ou caminho no Windows

# AI Models
WHISPER_MODEL=base  # tiny, base, small, medium, large
WHISPER_DEVICE=cpu  # ou cuda para GPU

# Gemini API Key
GOOGLE_API_KEY=
```

### Frontend (.env)

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
```

## Testando a Instalação

### Backend

```bash
# Health check
curl http://localhost:8000/health

# API docs
# Abra http://localhost:8000/docs no navegador
```

### Frontend

```bash
# Abra http://localhost:5173 no navegador
```

### Testar Transcrição

```python
from backend.src.agents.transcriber import transcricao_youtube_video

# Transcrever um vídeo
transcricao_youtube_video(
    url="https://www.youtube.com/watch?v=VIDEO_ID",
    temp_video_path="temp_video.mp4",
    model_size="base",
    output_file_path="transcription"
)
```

## Desenvolvimento

### Executar Testes

```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

### Linting

```bash
# Backend
black .
flake8 .

# Frontend
npm run lint
```

## Problemas Comuns

### FFmpeg não encontrado

- Verifique se o FFmpeg está instalado: `ffmpeg -version`
- Configure o caminho correto no `.env`

### Erro de conexão com banco de dados

- Verifique se o PostgreSQL está rodando
- Confirme as credenciais no `.env`
- Teste a conexão: `psql -U user -d cortai`

### Erro ao baixar vídeos

- Verifique sua conexão com a internet
- Alguns vídeos podem ter restrições regionais
- Atualize o yt-dlp: `pip install -U yt-dlp`

### Modelo Whisper muito lento

- Use um modelo menor: `WHISPER_MODEL=tiny` ou `base`
- Para melhor performance, use GPU: `WHISPER_DEVICE=cuda`
- Considere usar Whisper API da OpenAI para produção

## Próximos Passos

1. Leia a [Arquitetura](ARCHITECTURE.md)
2. Explore a [API Documentation](http://localhost:8000/docs)
3. Implemente os agentes restantes (Analyst, Editor)
4. Configure integrações com redes sociais
