from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import videos

app = FastAPI(
    title="CortAI API",
    description="API para automação de cortes de vídeo com IA Multimodal",
    version="1.0.0"
)

# Configuração CORS (Permite que o Frontend acesse a API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especifique a URL do frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rotas
app.include_router(videos.router, prefix="/api/v1/videos", tags=["videos"])

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "CortAI Backend"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)

