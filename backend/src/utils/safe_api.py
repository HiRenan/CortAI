import logging

# FUNÇÃO DE CHAMADA SEGURA AO LLM

def safe_llm_call(model, prompt):
    """
    Executa a chamada ao LLM de forma segura, capturando qualquer erro.
    
    Args:
        model: instância do Gemini (genai.GenerativeModel)
        prompt: str, prompt a ser enviado ao modelo

    Returns:
        tuple: 
            - resposta_texto (str | None): Texto retornado pelo modelo (ou None em caso de erro)
            - erro (str | None): Mensagem de erro, caso ocorra, ou None se sucesso

    Observações:
        - Garante que a aplicação principal não quebre com erros do LLM
        - Útil para integração com LangGraph, que espera sempre um retorno seguro
    """
    try:
        # Gera o conteúdo do LLM usando o prompt fornecido
        response = model.generate_content(prompt)

        # Retorna a resposta limpa
        return response.text.strip(), None

    except Exception as e:
        # Loga o erro e retorna mensagem segura
        logging.error(f"Erro na chamada ao LLM: {e}")
        return None, str(e)
