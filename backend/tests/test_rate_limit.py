import os
import time
import sys
from dotenv import load_dotenv

# Adiciona o diretório raiz ao path para importar os módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.analyst import RateLimitedGeminiEmbeddingFunction

def test_rate_limit():
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("ERRO: GOOGLE_API_KEY não encontrada.")
        return

    print("Iniciando teste de Rate Limit...")
    embedder = RateLimitedGeminiEmbeddingFunction(api_key=api_key)
    
    texts = ["Texto 1 para teste", "Texto 2 para teste", "Texto 3 para teste"]
    
    start_time = time.time()
    embeddings = embedder(texts)
    end_time = time.time()
    
    duration = end_time - start_time
    print(f"Duração total: {duration:.2f}s")
    print(f"Embeddings gerados: {len(embeddings)}")
    
    # Se processou 3 itens com 4.5s de delay cada, deve levar pelo menos 13.5s
    if duration >= 13:
        print("SUCESSO: O delay parece estar funcionando.")
    else:
        print("AVISO: Foi muito rápido. O rate limit pode não estar funcionando.")

if __name__ == "__main__":
    test_rate_limit()
