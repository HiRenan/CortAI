"""
Centraliza chamadas seguras a APIs externas (Gemini, YouTube, etc.)
Garantindo que qualquer exceção seja capturada e nunca quebre o fluxo do LangGraph.
"""

import logging

# Configuração básica do logger
log = logging.getLogger("safe_api")

# Mapeamento de finish_reason do Gemini API
FINISH_REASONS = {
    0: "UNSPECIFIED",
    1: "STOP",
    2: "MAX_TOKENS",
    3: "SAFETY",
    4: "RECITATION",
    5: "OTHER"
}


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
        # Log do tamanho do prompt para debugging
        prompt_size = len(prompt)
        log.info(f"Enviando prompt ao Gemini (tamanho: {prompt_size} caracteres)")

        response = model.generate_content(prompt)

        # Captura finish_reason e decodifica
        finish_reason_code = None
        finish_reason_name = "UNKNOWN"
        if response and response.candidates:
            try:
                finish_reason_code = response.candidates[0].finish_reason
                finish_reason_name = FINISH_REASONS.get(finish_reason_code, f"UNKNOWN({finish_reason_code})")
            except Exception:
                pass

        # Captura prompt_feedback (bloqueios antes da geração)
        prompt_feedback = None
        if response:
            try:
                prompt_feedback = response.prompt_feedback
            except Exception:
                pass

        # Captura safety_ratings
        safety_ratings = None
        if response and response.candidates:
            try:
                safety_ratings = response.candidates[0].safety_ratings
            except Exception:
                pass

        # Log detalhado do finish_reason
        log.info(f"Resposta recebida - finish_reason: {finish_reason_name} (code={finish_reason_code})")

        # Tratamento específico por finish_reason
        if finish_reason_code == 2:  # MAX_TOKENS
            error_msg = (
                f"Limite de tokens atingido (finish_reason=MAX_TOKENS). "
                f"O prompt ou a resposta esperada é muito longa. "
                f"Considere aumentar max_output_tokens ou dividir a transcrição em chunks menores."
            )
            log.warning(error_msg)
            return None, error_msg

        elif finish_reason_code == 3:  # SAFETY
            error_msg = f"Conteúdo bloqueado por filtros de segurança (finish_reason=SAFETY)."
            if safety_ratings:
                error_msg += f" Safety ratings: {safety_ratings}"
            log.warning(error_msg)
            return None, error_msg

        elif finish_reason_code == 4:  # RECITATION
            error_msg = "Conteúdo bloqueado por detecção de recitação (finish_reason=RECITATION)."
            log.warning(error_msg)
            return None, error_msg

        # Tenta extrair o texto com segurança
        text = None
        if response:
            try:
                text = response.text.strip()
            except Exception as inner:
                msg = f"LLM sem texto retornado (finish_reason={finish_reason_name})"
                inner_msg = str(inner).strip()
                if inner_msg:
                    msg = f"{msg}: {inner_msg}"
                if prompt_feedback:
                    msg += f" | prompt_feedback: {prompt_feedback}"
                log.error(msg)
                return None, msg

        if not text:
            msg = f"LLM retornou resposta vazia (finish_reason={finish_reason_name})"
            if prompt_feedback:
                msg += f" | prompt_feedback: {prompt_feedback}"
            log.warning(msg)
            return None, msg

        log.info(f"Resposta extraída com sucesso (tamanho: {len(text)} caracteres)")
        return text, None

    except Exception as e:
        log.exception(f"Erro durante chamada ao LLM: {e}")
        return None, str(e)
