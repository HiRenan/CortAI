import os  # Interage com o sistema operacional
import json  # Leitura/escrita de JSON
import logging  # Para logs detalhados
from dotenv import load_dotenv  # Carrega variáveis de ambiente do arquivo .env
import google.generativeai as genai  # Cliente oficial para acessar os modelos Gemini
from pydantic import BaseModel, ValidationError  # Validação rigorosa de dados estruturados
from typing import List, Optional, Dict, Any

# Função auxiliar para chamadas seguras ao LLM
from src.utils.safe_api import safe_llm_call
# Funções para chunking de transcrições longas
from src.utils.chunking import (
    create_chunks_from_segments,
    get_chunk_text,
    get_chunk_time_range
)

log = logging.getLogger("analyst")


# CONFIGURAÇÃO DO AMBIENTE E DA API GEMINI

# Carrega as variáveis do arquivo .env
load_dotenv()

# Obtém a API key do Gemini
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")

# Caso a chave não exista, lança erro imediatamente
if not GEMINI_API_KEY:
    raise ValueError("ERRO: variável GOOGLE_API_KEY não encontrada no arquivo .env!")

# Configura o cliente Gemini com a API key obtida
genai.configure(api_key=GEMINI_API_KEY)

# Configuração de tokens (pode ser sobrescrita via variável de ambiente)
MAX_OUTPUT_TOKENS = int(os.getenv("GEMINI_MAX_OUTPUT_TOKENS", "8192"))

# Safety settings para evitar bloqueios desnecessários em análises legítimas de vídeo
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]


# DEFINIÇÃO DO MODELO DA RESPOSTA (PYDANTIC)

class Highlight(BaseModel):
    """
    Estrutura de um único highlight gerado pelo modelo.

    Attributes:
        start (float): Tempo inicial em segundos.
        end (float): Tempo final em segundos.
        summary (Optional[str]): Descrição opcional do trecho.
        score (Optional[float]): Relevância opcional atribuída pelo modelo.
    """
    start: float
    end: float
    summary: Optional[str] = None
    score: Optional[float] = None


class AnalystOutput(BaseModel):
    """
    Estrutura completa da saída do agente analista.

    Attributes:
        highlights (List[Highlight]): Lista de todos os trechos importantes identificados.
    """
    highlights: List[Highlight]


# JSON Schema que será enviado ao Gemini para garantir saída 100% estruturada
JSON_SCHEMA = {
    "type": "object",
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
                "required": ["start", "end"]
            }
        }
    },
    "required": ["highlights"]
}


# CLASSE PRINCIPAL DO AGENTE ANALISTA

class AnalystAgent:
    """
    Agente responsável por analisar uma transcrição e identificar automaticamente
    o(s) trecho(s) mais relevante(s) do vídeo.

    Esta versão substitui completamente:
    - Regex
    - Parsing textual frágil
    - Timestamp HH:MM:SS
    - Conversão manual de tempo

    Agora:
    - O Gemini retorna **apenas JSON**
    - A estrutura é validada pelo **Pydantic**
    - O LangGraph recebe dados limpos, validados e prontos para uso

    Além disso:
    - Toda chamada ao LLM é protegida com try/except via `safe_llm_call`
    """

    def __init__(self, model_name="gemini-2.5-flash"):
        """
        Inicializa o modelo Gemini com um schema JSON obrigatório.

        Args:
            model_name (str): Nome do modelo Gemini a ser utilizado.
        """

        # Criamos o modelo com um schema que obriga JSON válido,
        # evitando respostas em formato textual solto.
        self.model = genai.GenerativeModel(
            model_name,
            generation_config={
                "temperature": 0.3,               # Garante consistência
                "max_output_tokens": MAX_OUTPUT_TOKENS,  # Aumentado de 2048 para 8192 (configurável via .env)
                "response_mime_type": "application/json",  # Obriga resposta JSON
                "response_schema": JSON_SCHEMA,   # Obriga estrutura definida acima
            },
            safety_settings=SAFETY_SETTINGS  # Configuração de filtros de segurança
        )

    # ==============================================================================================================
    def run(self, transcript: str):
        """
        Executa o agente analista para identificar highlights dentro da transcrição.

        Args:
            transcript (str): Texto completo da transcrição.

        Returns:
            tuple:
                - (AnalystOutput | None): Saída validada pelo Pydantic, se bem-sucedida.
                - (str | None): Mensagem de erro, caso ocorra falha.

        A função nunca lança exceções — sempre retorna um erro seguro,
        permitindo integração estável com o LangGraph.
        """

        # Prompt especializado enviado ao LLM
        prompt = f"""
Você é um especialista em análise de vídeos e precisa produzir uma saída
**TOTALMENTE ESTRUTURADA em JSON** contendo os melhores highlights do vídeo.

REGRAS IMPORTANTES:
- Retorne apenas JSON válido (nenhum texto fora do objeto JSON).
- Cada highlight deve conter:
    - start: tempo inicial em segundos (float/int)
    - end: tempo final em segundos (float/int)
    - summary: resumo opcional
    - score: pontuação opcional
- Nunca escreva texto solto, explicações ou comentários.
- Sempre garanta que start < end.

TRANSCRIÇÃO PARA ANÁLISE:
{transcript}
"""

        # CHAMADA SEGURA AO LLM (com try/except interno)

        llm_response, error = safe_llm_call(self.model, prompt)

        # Se ocorrer qualquer erro (timeout, erro de API, etc.), retornamos para o LangGraph como mensagem segura
        if error:
            return None, f"GeminiError: {error}"

        # PARSE DO JSON RETORNADO

        try:
            data = json.loads(llm_response)

        except Exception as e:
            # JSON inválido ou malformado
            return None, f"JSONDecodeError: {str(e)}"

        # VALIDAÇÃO E TIPAGEM COM PYDANTIC

        try:
            parsed = AnalystOutput(**data)
            return parsed, None  # Sucesso

        except ValidationError as e:
            # Gemini retornou JSON válido mas com campos errados
            return None, f"PydanticValidationError: {str(e)}"

    # ==============================================================================================================
    def run_chunked(
        self,
        segments: List[Dict[str, Any]],
        max_highlights: int = 5,
        chunk_duration_seconds: int = 360
    ):
        """
        Executa análise de transcrição longa usando estratégia Map-Reduce com chunking.

        Esta função é usada quando a transcrição é muito longa para processar de uma vez.
        Divide a transcrição em chunks temporais, analisa cada chunk individualmente,
        e depois consolida e ranqueia os melhores highlights.

        Args:
            segments: Lista de segments do Whisper com campos 'start', 'end', 'text'
            max_highlights: Número máximo de highlights a retornar (default: 5)
            chunk_duration_seconds: Duração de cada chunk em segundos (default: 360 = 6 min)

        Returns:
            tuple:
                - (AnalystOutput | None): Saída validada com os melhores highlights consolidados
                - (str | None): Mensagem de erro, caso ocorra falha

        Estratégia:
            1. MAP: Divide em chunks e analisa cada um separadamente
            2. REDUCE: Consolida todos os highlights e seleciona os N melhores
        """
        log.info(
            f"Iniciando análise chunked: {len(segments)} segments, "
            f"max_highlights={max_highlights}, chunk_duration={chunk_duration_seconds}s"
        )

        # FASE 1 - MAP: Dividir em chunks e processar cada um
        chunks = create_chunks_from_segments(segments, chunk_duration_seconds)

        if not chunks:
            return None, "Falha ao criar chunks da transcrição"

        log.info(f"Criados {len(chunks)} chunks para processamento")

        all_highlights = []

        for chunk_idx, chunk in enumerate(chunks):
            chunk_text = get_chunk_text(chunk)
            chunk_start, chunk_end = get_chunk_time_range(chunk)

            log.info(
                f"Processando chunk {chunk_idx + 1}/{len(chunks)} "
                f"(tempo: {chunk_start:.1f}s - {chunk_end:.1f}s, "
                f"{len(chunk_text)} chars)"
            )

            # Prompt para análise do chunk
            prompt = f"""
Você é um especialista em análise de vídeos. Analise este trecho de transcrição
e identifique os 3-5 MELHORES momentos virais/highlights.

IMPORTANTE:
- Este é um trecho de um vídeo maior (tempo {chunk_start:.1f}s a {chunk_end:.1f}s)
- Os timestamps devem estar DENTRO deste intervalo
- Retorne apenas JSON válido
- Cada highlight deve ter: start, end, summary, score (0-100)
- Ordene por relevância (score mais alto primeiro)
- Priorize momentos emocionantes, engraçados, informativos ou impactantes

TRECHO DA TRANSCRIÇÃO:
{chunk_text}
"""

            # Processar chunk
            llm_response, error = safe_llm_call(self.model, prompt)

            if error:
                log.warning(f"Erro no chunk {chunk_idx + 1}: {error}")
                continue  # Pula este chunk e continua com os outros

            # Parse e validação
            try:
                data = json.loads(llm_response)
                chunk_output = AnalystOutput(**data)

                # Adiciona highlights deste chunk à lista global
                for highlight in chunk_output.highlights:
                    # Validação: garantir que timestamps estão dentro do chunk
                    if highlight.start >= chunk_start and highlight.end <= chunk_end + 5:  # +5s de margem
                        all_highlights.append(highlight)
                        log.debug(
                            f"  Highlight encontrado: {highlight.start:.1f}s-{highlight.end:.1f}s "
                            f"(score: {highlight.score})"
                        )
                    else:
                        log.warning(
                            f"  Highlight fora do intervalo ignorado: "
                            f"{highlight.start:.1f}s-{highlight.end:.1f}s"
                        )

            except Exception as e:
                log.warning(f"Erro ao processar resposta do chunk {chunk_idx + 1}: {str(e)}")
                continue

        # Verifica se encontrou algum highlight
        if not all_highlights:
            return None, "Nenhum highlight encontrado em nenhum chunk"

        log.info(f"Total de highlights encontrados: {len(all_highlights)}")

        # FASE 2 - REDUCE: Consolidar e selecionar os melhores
        final_highlights = self._consolidate_and_rank_highlights(
            all_highlights,
            max_highlights
        )

        log.info(f"Highlights finais selecionados: {len(final_highlights)}")

        # Retorna resultado final
        result = AnalystOutput(highlights=final_highlights)
        return result, None

    # ==============================================================================================================
    def _consolidate_and_rank_highlights(
        self,
        highlights: List[Highlight],
        max_highlights: int
    ) -> List[Highlight]:
        """
        Consolida e ranqueia highlights para selecionar os N melhores.

        Estratégia:
        1. Remove duplicatas (highlights muito próximos)
        2. Ordena por score
        3. Garante diversidade temporal (evita concentrar todos no início)
        4. Seleciona os top N

        Args:
            highlights: Lista de todos os highlights encontrados
            max_highlights: Número máximo de highlights a retornar

        Returns:
            Lista de highlights consolidados e ranqueados
        """
        if not highlights:
            return []

        log.info(f"Consolidando {len(highlights)} highlights para {max_highlights} finais")

        # 1. Atribuir score padrão se não houver
        for h in highlights:
            if h.score is None:
                h.score = 50.0  # Score neutro

        # 2. Ordenar por score (maior para menor)
        sorted_highlights = sorted(highlights, key=lambda h: h.score or 0, reverse=True)

        # 3. Remover overlaps/duplicatas
        deduplicated = []
        for highlight in sorted_highlights:
            # Verifica se este highlight já está muito próximo de algum já selecionado
            is_duplicate = False
            for selected in deduplicated:
                # Se há overlap significativo (>70%), considera duplicata
                overlap = self._calculate_overlap(highlight, selected)
                if overlap > 0.7:
                    is_duplicate = True
                    log.debug(
                        f"Highlight duplicado ignorado: {highlight.start:.1f}s-{highlight.end:.1f}s "
                        f"(overlap {overlap:.2%} com {selected.start:.1f}s-{selected.end:.1f}s)"
                    )
                    break

            if not is_duplicate:
                deduplicated.append(highlight)

        # 4. Garantir diversidade temporal se temos muitos highlights
        if len(deduplicated) > max_highlights * 2:
            deduplicated = self._ensure_temporal_diversity(deduplicated, max_highlights)

        # 5. Selecionar top N
        final = deduplicated[:max_highlights]

        # 6. Ordenar por timestamp (para facilitar edição)
        final.sort(key=lambda h: h.start)

        log.info(
            f"Consolidação concluída: {len(final)} highlights finais "
            f"(de {len(highlights)} originais)"
        )

        return final

    # ==============================================================================================================
    def _calculate_overlap(self, h1: Highlight, h2: Highlight) -> float:
        """
        Calcula a proporção de overlap entre dois highlights.

        Returns:
            Float entre 0.0 (sem overlap) e 1.0 (overlap total)
        """
        # Encontra o intervalo de interseção
        overlap_start = max(h1.start, h2.start)
        overlap_end = min(h1.end, h2.end)

        # Se não há overlap
        if overlap_start >= overlap_end:
            return 0.0

        # Calcula overlap como proporção do menor highlight
        overlap_duration = overlap_end - overlap_start
        h1_duration = h1.end - h1.start
        h2_duration = h2.end - h2.start
        smaller_duration = min(h1_duration, h2_duration)

        return overlap_duration / smaller_duration if smaller_duration > 0 else 0.0

    # ==============================================================================================================
    def _ensure_temporal_diversity(
        self,
        highlights: List[Highlight],
        target_count: int
    ) -> List[Highlight]:
        """
        Garante que os highlights estejam distribuídos ao longo do vídeo.

        Evita pegar todos os highlights do início e ignora o resto.

        Args:
            highlights: Lista de highlights ordenados por score
            target_count: Número alvo de highlights

        Returns:
            Lista com highlights mais diversificados temporalmente
        """
        if len(highlights) <= target_count:
            return highlights

        # Divide o vídeo em "buckets" temporais
        num_buckets = min(target_count, 5)  # Máximo 5 buckets
        video_duration = max(h.end for h in highlights)
        bucket_duration = video_duration / num_buckets

        # Agrupa highlights por bucket
        buckets = [[] for _ in range(num_buckets)]
        for h in highlights:
            bucket_idx = min(int(h.start / bucket_duration), num_buckets - 1)
            buckets[bucket_idx].append(h)

        # Seleciona os melhores de cada bucket
        selected = []
        highlights_per_bucket = max(1, target_count // num_buckets)

        for bucket in buckets:
            if bucket:
                # Pega os top N deste bucket
                bucket_sorted = sorted(bucket, key=lambda h: h.score or 0, reverse=True)
                selected.extend(bucket_sorted[:highlights_per_bucket])

        # Se ainda falta, completa com os melhores restantes
        if len(selected) < target_count:
            remaining = [h for h in highlights if h not in selected]
            remaining_sorted = sorted(remaining, key=lambda h: h.score or 0, reverse=True)
            selected.extend(remaining_sorted[:target_count - len(selected)])

        # Reordena por score final
        selected.sort(key=lambda h: h.score or 0, reverse=True)

        return selected[:target_count]
