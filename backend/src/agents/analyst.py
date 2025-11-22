import os  # Interage com o sistema operacional
import json  # Leitura/escrita de JSON
from dotenv import load_dotenv  # Carrega variáveis de ambiente do arquivo .env
import google.generativeai as genai  # Cliente oficial para acessar os modelos Gemini
from pydantic import BaseModel, ValidationError  # Validação rigorosa de dados estruturados
from typing import List, Optional

# Função auxiliar para chamadas seguras ao LLM (será criada em utils/safe_api.py)
from backend.src.utils.safe_api import safe_llm_call


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
                "max_output_tokens": 2048,        # Tamanho máximo da saída
                "response_mime_type": "application/json",  # Obriga resposta JSON
                "response_schema": JSON_SCHEMA,   # Obriga estrutura definida acima
            }
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
