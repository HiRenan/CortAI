"""
Script de teste básico para validar os agentes CortAI isoladamente.
Execute com: python test_agents.py
"""
import sys
import os

# Adiciona o diretório src ao path para imports funcionarem
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_config():
    """Testa se a configuração está correta"""
    print("\n=== Teste 1: Configuracao ===")
    try:
        from core.config import (
            DATA_DIR,
            STORAGE_DIR,
            GOOGLE_API_KEY,
            FFMPEG_PATH
        )
        print(f"[OK] Diretorio data: {DATA_DIR}")
        print(f"[OK] Diretorio storage: {STORAGE_DIR}")
        print(f"[OK] Google API Key: {GOOGLE_API_KEY[:20]}...")
        print(f"[OK] FFmpeg Path: {FFMPEG_PATH}")
        return True
    except Exception as e:
        print(f"[ERRO] Erro na configuracao: {e}")
        return False


def test_imports():
    """Testa se todos os módulos podem ser importados"""
    print("\n=== Teste 2: Imports ===")
    try:
        from agents.transcriber import transcricao_youtube_video
        print("✓ Transcriber Agent importado")

        from agents.analyst import executar_agente_analista
        print("✓ Analyst Agent importado")

        from agents.editor import executar_agente_editor
        print("✓ Editor Agent importado")

        from core.graph import build_graph
        print("✓ LangGraph workflow importado")

        return True
    except Exception as e:
        print(f"✗ Erro ao importar módulos: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_graph_build():
    """Testa se o grafo LangGraph pode ser construído"""
    print("\n=== Teste 3: Build do Grafo LangGraph ===")
    try:
        from core.graph import build_graph
        graph = build_graph()
        print("✓ Grafo LangGraph construído com sucesso")
        print(f"✓ Tipo do grafo: {type(graph)}")
        return True
    except Exception as e:
        print(f"✗ Erro ao construir grafo: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_gemini_connection():
    """Testa conexão com Google Gemini"""
    print("\n=== Teste 4: Conexão com Google Gemini ===")
    try:
        import google.generativeai as genai
        from core.config import GOOGLE_API_KEY

        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel("gemini-2.5-flash")

        # Teste simples
        response = model.generate_content("Diga olá em português.")
        print(f"✓ Conexão com Gemini OK")
        print(f"✓ Resposta de teste: {response.text[:50]}...")
        return True
    except Exception as e:
        print(f"✗ Erro ao conectar com Gemini: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_directories():
    """Verifica se os diretórios existem"""
    print("\n=== Teste 5: Diretórios ===")
    try:
        from core.config import DATA_DIR, STORAGE_DIR

        if DATA_DIR.exists():
            print(f"✓ Diretório data/ existe: {DATA_DIR}")
        else:
            print(f"✗ Diretório data/ NÃO existe: {DATA_DIR}")
            return False

        if STORAGE_DIR.exists():
            print(f"✓ Diretório storage/ existe: {STORAGE_DIR}")
        else:
            print(f"✗ Diretório storage/ NÃO existe: {STORAGE_DIR}")
            return False

        return True
    except Exception as e:
        print(f"✗ Erro ao verificar diretórios: {e}")
        return False


def main():
    """Executa todos os testes"""
    print("="*60)
    print("CortAI - Teste Básico dos Agentes")
    print("="*60)

    tests = [
        ("Configuração", test_config),
        ("Imports", test_imports),
        ("Diretórios", test_directories),
        ("Build do Grafo", test_graph_build),
        ("Conexão Gemini", test_gemini_connection),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ Erro fatal no teste '{name}': {e}")
            results.append((name, False))

    # Resumo
    print("\n" + "="*60)
    print("RESUMO DOS TESTES")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASSOU" if result else "✗ FALHOU"
        print(f"{name:.<40} {status}")

    print("="*60)
    print(f"Resultado: {passed}/{total} testes passaram")
    print("="*60)

    if passed == total:
        print("\n🎉 Todos os testes passaram! Sistema pronto para uso.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} teste(s) falharam. Verifique os erros acima.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
