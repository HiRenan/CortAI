"""
Centraliza chamadas seguras a APIs externas (Gemini, YouTube, etc.)
Garantindo que qualquer exceção seja capturada e nunca quebre o fluxo do LangGraph.
"""

import logging

# Configuração básica do logger
log = logging.getLogger("safe_api")


# CHAMADA SEGURA A MODELOS LLM (GEMINI)
def safe_llm_call(model, prompt: str):
    """
    Executa uma chamada segura ao modelo Gemini.

    Args:
        model: instância de google.generativeai.GenerativeModel
        prompt (str): texto enviado ao LLM

    Returns:
        tuple:
            (response_text | None, error_message | None)
    """
    try:
        response = model.generate_content(prompt)
        text = response.text.strip() if response and hasattr(response, "text") else None

        if not text:
            return None, "LLM retornou resposta vazia ou sem campo 'text'."

        return text, None

    except Exception as e:
        log.exception(f"Erro durante chamada ao LLM: {e}")
        return None, str(e)
