"""
Testes unitários para o AnalystAgent com saída estruturada via Pydantic.
"""

import pytest
import json
from src.agents.analyst import AnalystAgent


# TESTE: Execução do agente com mock do LLM
def test_analyst_agent_parsing(monkeypatch):
    """
    Verifica se o AnalystAgent consegue:
    - Receber um JSON estruturado (mockado)
    - Validar via Pydantic
    - Retornar o modelo e nenhum erro
    """

    # Simulação de retorno válido do LLM
    mock_llm_json_response = json.dumps({
        "highlights": [
            {
                "start": 30,
                "end": 75,
                "summary": "Momento mais impactante do vídeo.",
                "score": 0.92
            }
        ]
    })

    # Monkeypatch substitui safe_llm_call → (mock, None)
    from src.utils import safe_api

    def fake_safe_call(model, prompt):
        return mock_llm_json_response, None

    monkeypatch.setattr(safe_api, "safe_llm_call", fake_safe_call)

    # Executa o agente
    agent = AnalystAgent()
    output, error = agent.run("transcrição simulada")

    # Verificações
    assert error is None
    assert output is not None
    assert len(output.highlights) == 1

    h = output.highlights[0]
    assert h.start == 30
    assert h.end == 75
    assert h.summary == "Momento mais impactante do vídeo."
    assert h.score == 0.92


# TESTE: LLM retorna erro → AnalystAgent deve retornar erro
def test_analyst_agent_llm_error(monkeypatch):

    from src.utils import safe_api

    # Simula falha do LLM
    def fake_safe_call_err(model, prompt):
        return None, "Falha simulada no LLM"

    monkeypatch.setattr(safe_api, "safe_llm_call", fake_safe_call_err)

    agent = AnalystAgent()
    output, error = agent.run("texto qualquer")

    assert output is None
    assert error == "Falha simulada no LLM"


# TESTE: JSON inválido enviado pelo LLM
def test_analyst_agent_invalid_json(monkeypatch):

    from src.utils import safe_api

    # LLM retorna JSON mal-formado
    def fake_safe_call_invalid(model, prompt):
        return "{ invalid json ", None

    monkeypatch.setattr(safe_api, "safe_llm_call", fake_safe_call_invalid)

    agent = AnalystAgent()
    output, error = agent.run("texto qualquer")

    assert output is None
    assert "Erro ao fazer parse do JSON retornado pelo LLM" in error
