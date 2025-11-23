import os # Interage com o Sistema Operacional
import json # Manipulação de arquivos JSON
import logging # Registro de logs
import shutil # Copia e move arquivos
import uuid # Geração de identificadores únicos
from typing import List, Optional, Dict, Any # Tipagem estática
from dotenv import load_dotenv # Carrega variáveis de ambiente
import google.generativeai as genai # Importa o modelo de linguagem do Google (Gemini)
from pydantic import BaseModel, ValidationError #
import time # Controle de tempo
import chromadb # Banco de Dados Vetorial
from chromadb.utils import embedding_functions # Função de embedding

# Configuração de logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("analyst_agent")

# Carrega variáveis de ambiente e obtem a chave de API do Gemini
load_dotenv()
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("ERRO: variável GOOGLE_API_KEY não encontrada no .env!")

# Configura o modelo com a chave de API
genai.configure(api_key=GEMINI_API_KEY)

# -----------------------------------------------------------------------------------------------------------------

class Highlight(BaseModel):
    """
    Estrutura de um highlight identificado.
    """
    start: float
    end: float
    summary: str # Resumo do highlight
    score: float # Score do highlight

# -----------------------------------------------------------------------------------------------------------------

class RateLimitedGeminiEmbeddingFunction(embedding_functions.EmbeddingFunction):
    """
    Função de embedding customizada para o Gemini com Rate Limiting.
    O plano gratuito permite apenas 15 RPM (Requisições Por Minuto).
    Esta classe garante um intervalo seguro entre as chamadas.
    """
    def __init__(self, api_key: str, model_name: str = "models/text-embedding-004"):
        self.api_key = api_key
        self.model_name = model_name
        genai.configure(api_key=api_key)

    def __call__(self, input: List[str]) -> List[List[float]]:
        embeddings = []
        total = len(input)
        
        for i, text in enumerate(input):
            logger.info(f"Gerando embedding {i+1}/{total}...")
            retry_count = 0
            
            while True:
                try:
                    # Substitui textos vazios por placeholder para evitar erro da API
                    if not isinstance(text, str) or not text.strip():
                        logger.warning(f"Input de embedding vazio no índice {i}. Usando placeholder.")
                        text_to_embed = "[no_text]"
                    else:
                        text_to_embed = text

                    # Delay preventivo de 4.5s (garante ~13 RPM, abaixo do limite de 15)
                    # O primeiro também espera para garantir intervalo com requisições anteriores
                    time.sleep(4.5)

                    result = genai.embed_content(
                        model=self.model_name,
                        content=text_to_embed,
                        task_type="retrieval_document"
                    )
                    embeddings.append(result['embedding'])
                    break
                    
                except Exception as e:
                    error_msg = str(e)
                    if "429" in error_msg or "ResourceExhausted" in error_msg:
                        if retry_count >= 3:
                            logger.error("Máximo de tentativas (3) excedido para rate limit.")
                            raise e
                            
                        wait_time = 60 # Espera 1 minuto se tomar 429
                        logger.warning(f"Rate limit (429) atingido. Aguardando {wait_time}s... (Tentativa {retry_count+1}/3)")
                        time.sleep(wait_time)
                        retry_count += 1
                    else:
                        logger.error(f"Erro não tratado no embedding: {e}")
                        raise e
                        
        return embeddings

# -----------------------------------------------------------------------------------------------------------------

class AnalystOutput(BaseModel):
    """
    Saída estruturada do agente analista.
    """

    # Lista de highlights identificados
    highlights: List[Highlight]

# -----------------------------------------------------------------------------------------------------------------

# Schema JSON para forçar saída estruturada do Gemini
JSON_SCHEMA = {
    "type": "object", # Tipo de dados
    "properties": {
        "highlights": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "start": {"type": "number"},
                    "end": {"type": "number"},
                    "summary": {"type": "string"},
                    "score": {"type": "number"},
                },
                "required": ["start", "end", "summary", "score"]
            }
        }
    },
    "required": ["highlights"] # Campos obrigatórios
}

# -----------------------------------------------------------------------------------------------------------------

class AnalystAgent:
    """
    Agente Analista com RAG (Retrieval-Augmented Generation).
    
    Fluxo:
    1. Recebe a transcrição completa (JSON).
    2. Divide em chunks (trechos) com timestamps.
    3. Gera embeddings para cada chunk.
    4. Armazena no ChromaDB.
    5. Busca os chunks mais relevantes para critérios de "viralidade" e "impacto".
    6. Envia apenas os chunks relevantes para o LLM decidir o corte final.
    """

    def __init__(self, model_name="gemini-2.5-flash"):
        self.model_name = model_name # Nome do modelo
        self.chroma_client = chromadb.Client() # Cliente em memória (efêmero para cada job)
        
        # Configura o modelo Gemini para geração
        self.model = genai.GenerativeModel(
            model_name,
            generation_config={
                "temperature": 0.2,
                "response_mime_type": "application/json", # Tipo de resposta
                "response_schema": JSON_SCHEMA,
            }
        )

        # Configura função de embedding customizada com Rate Limit
        self.embedding_fn = RateLimitedGeminiEmbeddingFunction(
            api_key=GEMINI_API_KEY,
            model_name="models/text-embedding-004" # Modelo de embedding mais recente
        )

    def _chunk_transcription(self, transcription_data: Dict, chunk_size_seconds: int = 60) -> List[Dict]:
        """
        Divide a transcrição em chunks baseados em tempo.
        """

        # Obtem os segmentos da transcrição
        segments = transcription_data.get("segments", [])
        if not segments:
            # Fallback se não houver segmentos detalhados: usa o texto inteiro como um chunk
            return [{"text": transcription_data.get("text", ""), "start": 0, "end": 0}]

        # Lista de chunks
        chunks = []
        current_chunk = []
        current_start = segments[0].get("start", 0)
        current_text_len = 0
        
        for seg in segments:
            start = seg.get("start", 0)
            end = seg.get("end", 0)
            text = seg.get("text", "")
            
            # Se o chunk atual já passou do tamanho desejado, fecha o chunk
            if (end - current_start) > chunk_size_seconds and current_chunk:
                # Junta os segmentos do chunk atual
                chunk_text = " ".join([s["text"] for s in current_chunk])
                
                # Adiciona o chunk à lista de chunks
                chunks.append({
                    "text": chunk_text,
                    "start": current_start,
                    "end": current_chunk[-1]["end"]
                })
                
                # Inicia um novo chunk
                current_chunk = []

                # Atualiza o start do chunk atual
                current_start = start
            
            current_chunk.append(seg)

        # Adiciona o último chunk
        if current_chunk:
            # Junta os segmentos do chunk atual
            chunk_text = " ".join([s["text"] for s in current_chunk])
            
            # Adiciona o chunk à lista de chunks
            chunks.append({
                "text": chunk_text,
                "start": current_start,
                "end": current_chunk[-1]["end"]
            })
            
        return chunks

    def _index_chunks(self, chunks: List[Dict], collection_name: str):
        """
        Indexa os chunks no ChromaDB.
        """

        # Cria uma coleção no ChromaDB
        collection = self.chroma_client.get_or_create_collection(
            name=collection_name, # Nome da coleção
            embedding_function=self.embedding_fn # Função de embedding
        )

        # Cria IDs para os chunks
        ids = [str(i) for i in range(len(chunks))]
        
        # Cria documentos para os chunks
        documents = [c["text"] for c in chunks]
        
        # Cria metadados para os chunks
        metadatas = [{"start": c["start"], "end": c["end"]} for c in chunks]
        # Filtra documentos vazios para evitar erros ao gerar embeddings
        filtered_docs = []
        filtered_meta = []
        filtered_ids = []

        for i, doc in enumerate(documents):
            if isinstance(doc, str) and doc.strip():
                filtered_docs.append(doc)
                filtered_meta.append(metadatas[i])
                filtered_ids.append(ids[i])
            else:
                logger.warning(f"Chunk {i} vazio. Pulando indexação desse chunk.")

        # Se não houver documentos não vazios, não adiciona nada
        if not filtered_docs:
            logger.warning("Nenhum chunk não-vazio para indexar; coleção criada sem registros.")
            return collection

        # Adiciona os chunks filtrados à coleção
        collection.add(
            documents=filtered_docs,
            metadatas=filtered_meta,
            ids=filtered_ids
        )
        return collection

    def run(self, transcription_path: str) -> Dict:
        """
        Executa o pipeline de análise com RAG.
        """
        logger.info(f"Iniciando análise RAG para: {transcription_path}")

        # Carregar Transcrição
        with open(transcription_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Chunking
        chunks = self._chunk_transcription(data)
        logger.info(f"Transcrição dividida em {len(chunks)} chunks.")

        # Indexação (RAG)
        collection_name = f"job_{uuid.uuid4().hex}"
        collection = self._index_chunks(chunks, collection_name)
        
        # Retrieval (Busca pelos momentos mais interessantes)
        # Consultas focadas em diferentes aspectos de viralidade
        queries = [
            "momento mais engraçado ou piada",
            "discussão intensa ou polêmica",
            "conclusão surpreendente ou plot twist",
            "informação técnica valiosa ou tutorial",
            "momento emocionante ou inspirador"
        ]

        # Busca pelos momentos mais interessantes
        retrieved_docs = set()
        context_chunks = []

        for query in queries:
            try:
                results = collection.query(
                    query_texts=[query],
                    n_results=2 # Pega os top 2 de cada categoria
                )
            except Exception as e:
                logger.warning(f"Erro na query do ChromaDB para '{query}': {e}")
                continue

            # Valida estrutura retornada para evitar IndexError
            docs_outer = results.get('documents') if isinstance(results, dict) else None
            ids_outer = results.get('ids') if isinstance(results, dict) else None
            metas_outer = results.get('metadatas') if isinstance(results, dict) else None

            if not docs_outer or not isinstance(docs_outer, list) or not docs_outer[0]:
                logger.debug(f"Nenhum documento recuperado para a query: '{query}'")
                continue

            # Adiciona os chunks mais relevantes ao contexto (com proteção contra índices inválidos)
            for i, doc in enumerate(docs_outer[0]):
                try:
                    doc_id = ids_outer[0][i]
                    meta = metas_outer[0][i]
                except Exception:
                    logger.debug(f"Ignorando resultado inconsistente na query '{query}' index {i}")
                    continue

                if doc_id not in retrieved_docs:
                    context_chunks.append({
                        "text": doc,   # Texto do chunk
                        "start": meta.get("start", 0), # Início do chunk
                        "end": meta.get("end", 0) # Fim do chunk
                    })
                    retrieved_docs.add(doc_id)

        # Ordena chunks por tempo para manter coerência narrativa no prompt
        context_chunks.sort(key=lambda x: x["start"]) if context_chunks else None

        # Se não houver contexto recuperado, retorna fallback sem chamar o LLM
        if not context_chunks:
            logger.warning("Nenhum chunk recuperado para composição de prompt; retornando fallback.")
            try:
                self.chroma_client.delete_collection(collection_name)
            except Exception:
                pass
            return {
                "highlight_inicio_segundos": 0,
                "highlight_fim_segundos": 60,
                "resposta_bruta": "Fallback: transcrição vazia ou sem conteúdo recuperável."
            }

        # Montagem do Prompt com Contexto Recuperado
        context_text = ""
        for c in context_chunks:
            context_text += f"[{c['start']:.2f}s - {c['end']:.2f}s]: {c['text']}\n\n"

        prompt = f"""
                Você é um editor de vídeo especialista em cortes virais (TikTok/Reels/Shorts).
                Abaixo estão os trechos MAIS RELEVANTES recuperados de um vídeo longo.

                Sua tarefa é selecionar o MELHOR intervalo contínuo para um vídeo curto (entre 30s e 90s).

                TRECHOS RECUPERADOS (Contexto):
                {context_text}

                CRITÉRIOS:
                1. O corte deve ter início, meio e fim (faça sentido sozinho).
                2. Priorize momentos de alto engajamento (humor, polêmica, surpresa).
                3. O tempo total deve ser idealmente entre 30 e 90 segundos.

                Retorne APENAS o JSON conforme o schema.
                """

        try:
            response = self.model.generate_content(prompt) # Geração com LLM
            result_json = json.loads(response.text) # Resultado da geração

            # Validação Pydantic
            validated = AnalystOutput(**result_json)

            # Se o LLM não retornar highlights, trata como fallback
            if not validated.highlights:
                logger.warning("LLM retornou estrutura vazia de highlights; retornando fallback.")
                try:
                    self.chroma_client.delete_collection(collection_name)
                except Exception:
                    pass
                return {
                    "highlight_inicio_segundos": 0,
                    "highlight_fim_segundos": 60,
                    "resposta_bruta": "Fallback: LLM não retornou highlights válidos."
                }

            # Pega o melhor highlight (o primeiro ou o com maior score)
            best_highlight = validated.highlights[0]

            # Limpa o banco vetorial
            self.chroma_client.delete_collection(collection_name)

            # Retorna o resultado
            return {
                "highlight_inicio_segundos": best_highlight.start,
                "highlight_fim_segundos": best_highlight.end,
                "resposta_bruta": best_highlight.summary
            }

        except ValidationError as ve:
            logger.error(f"Validação Pydantic falhou: {ve}")
        except Exception as e: # Tratamento de erros
            logger.error(f"Erro na geração do highlight: {e}")

        # Fallback seguro padrão
        try:
            self.chroma_client.delete_collection(collection_name)
        except Exception:
            pass
        return {
            "highlight_inicio_segundos": 0,
            "highlight_fim_segundos": 60,
            "resposta_bruta": "Fallback: Erro na análise inteligente."
        }

# -------------------------------------------------------------------------------------------------------------

def executar_agente_analista(input_json: str, output_json: str) -> Dict:
    """
    Wrapper para manter compatibilidade com o worker existente.
    Instancia a classe AnalystAgent e executa o fluxo.
    """

    # Carrega o arquivo de transcrição
    with open(input_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Instancia o agente
    agent = AnalystAgent()
    
    # Executa o agente
    resultado = agent.run(input_json)
    
    # Garante que o diretório de saída existe antes de salvar o resultado
    output_dir = os.path.dirname(output_json)
    if output_dir:
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            logger.warning(f"Não foi possível criar diretório de saída {output_dir}: {e}")

    # Salva o resultado no disco (como o worker espera)
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=4)
    
    # Retorna o resultado
    return resultado
