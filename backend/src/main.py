from fastapi import FastAPI
import logging

log = logging.getLogger("backend.main")


app = FastAPI(title="CortAI API")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/")
async def root():
    return {"service": "CortAI", "status": "running"}


# Nota: rotas mais pesadas (vídeos, auth) não são automaticamente incluídas aqui
# para evitar falhas de import durante o carregamento do ASGI app. Podemos
# incluir essas rotas posteriormente ou corrigir imports de módulos que
# provocam erros (ex.: imports relativos em `src/graphs/main_graph.py`).
