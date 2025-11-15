# API Documentation - CortAI

## Base URL

```
Development: http://localhost:8000
Production: https://api.cortai.com
```

## Autenticação

A API usa JWT (JSON Web Tokens) para autenticação.

```http
Authorization: Bearer <token>
```

## Endpoints

### Health Check

```http
GET /health
```

Verifica o status da API.

**Response:**
```json
{
  "status": "ok",
  "version": "0.1.0"
}
```

---

## Videos

### Processar Vídeo

```http
POST /api/v1/videos/process
```

Inicia o processamento de um vídeo.

**Request Body:**
```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "options": {
    "transcribe": true,
    "analyze": true,
    "generate_clips": true,
    "whisper_model": "base"
  }
}
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "video_id": "123",
  "created_at": "2024-01-01T00:00:00Z"
}
```

---

### Listar Vídeos

```http
GET /api/v1/videos
```

Lista todos os vídeos processados.

**Query Parameters:**
- `page` (int): Número da página (default: 1)
- `limit` (int): Itens por página (default: 20)
- `status` (string): Filtrar por status (processing, completed, failed)

**Response:**
```json
{
  "videos": [
    {
      "id": "123",
      "title": "Video Title",
      "url": "https://youtube.com/watch?v=...",
      "status": "completed",
      "duration": 3600,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 100,
  "page": 1,
  "pages": 5
}
```

---

### Obter Vídeo

```http
GET /api/v1/videos/{video_id}
```

Retorna detalhes de um vídeo específico.

**Response:**
```json
{
  "id": "123",
  "title": "Video Title",
  "url": "https://youtube.com/watch?v=...",
  "status": "completed",
  "duration": 3600,
  "transcription": {
    "id": "456",
    "language": "pt-BR",
    "segments": 150
  },
  "clips": [
    {
      "id": "789",
      "start_time": 120,
      "end_time": 180,
      "score": 0.95
    }
  ],
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:05:00Z"
}
```

---

## Transcrições

### Obter Transcrição

```http
GET /api/v1/videos/{video_id}/transcription
```

Retorna a transcrição completa de um vídeo.

**Response:**
```json
{
  "id": "456",
  "video_id": "123",
  "language": "pt-BR",
  "segments": [
    {
      "id": 0,
      "start": 0.0,
      "end": 5.5,
      "text": "Texto transcrito aqui"
    }
  ],
  "created_at": "2024-01-01T00:00:00Z"
}
```

---

## Clipes

### Listar Clipes

```http
GET /api/v1/clips
```

Lista todos os clipes gerados.

**Query Parameters:**
- `video_id` (string): Filtrar por vídeo
- `min_score` (float): Score mínimo (0-1)
- `sort` (string): Ordenar por (score, duration, created_at)

**Response:**
```json
{
  "clips": [
    {
      "id": "789",
      "video_id": "123",
      "title": "Momento Destacado",
      "start_time": 120,
      "end_time": 180,
      "duration": 60,
      "score": 0.95,
      "url": "/storage/clips/789.mp4",
      "thumbnail": "/storage/thumbnails/789.jpg"
    }
  ],
  "total": 25
}
```

---

### Gerar Clipe Manual

```http
POST /api/v1/clips
```

Cria um clipe manualmente.

**Request Body:**
```json
{
  "video_id": "123",
  "start_time": 120,
  "end_time": 180,
  "title": "Meu Clipe",
  "add_subtitles": true
}
```

**Response:**
```json
{
  "id": "789",
  "status": "processing",
  "job_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

### Baixar Clipe

```http
GET /api/v1/clips/{clip_id}/download
```

Baixa o arquivo do clipe.

**Response:**
- Arquivo MP4 (video/mp4)

---

## Jobs

### Status do Job

```http
GET /api/v1/jobs/{job_id}
```

Verifica o status de um job de processamento.

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "type": "video_processing",
  "status": "completed",
  "progress": 100,
  "result": {
    "video_id": "123",
    "clips_generated": 5
  },
  "error": null,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:05:00Z"
}
```

---

## WebSocket

### Conectar

```
ws://localhost:8000/ws
```

Recebe atualizações em tempo real sobre processamento de vídeos.

**Mensagens:**

```json
{
  "type": "job_update",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "progress": 45
}
```

```json
{
  "type": "job_completed",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "video_id": "123",
  "clips_count": 5
}
```

---

## Códigos de Status

- `200` - OK
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

## Rate Limiting

- 100 requisições por minuto por IP
- 1000 requisições por hora por usuário autenticado

## Exemplos

### Python

```python
import requests

url = "http://localhost:8000/api/v1/videos/process"
data = {
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "options": {
        "transcribe": True,
        "analyze": True
    }
}

response = requests.post(url, json=data)
job = response.json()
print(f"Job ID: {job['job_id']}")
```

### JavaScript

```javascript
const response = await fetch('http://localhost:8000/api/v1/videos/process', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
    options: {
      transcribe: true,
      analyze: true
    }
  })
});

const job = await response.json();
console.log(`Job ID: ${job.job_id}`);
```

---

Para documentação interativa, acesse: http://localhost:8000/docs
