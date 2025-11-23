# API Documentation - CortAI

Documentação real da API está disponível em `/docs` (Swagger gerado pela aplicação).
Use os endpoints de vídeos:
- `POST /api/v1/videos/process`
- `GET /api/v1/videos/` (lista do usuário autenticado)
- `GET /api/v1/videos/status/{task_id}`
- `GET /api/v1/videos/{video_id}/download`

Demais endpoints descritos aqui estão planejados e não estão implementados no backend atual.
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
