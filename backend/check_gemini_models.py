"""
Script para listar modelos Gemini disponíveis
"""
import os
import sys
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    print("ERRO: GOOGLE_API_KEY não encontrada!")
    sys.exit(1)

print(f"API Key: {GOOGLE_API_KEY[:20]}...")
print("\nListando modelos disponíveis...\n")

genai.configure(api_key=GOOGLE_API_KEY)

try:
    models = genai.list_models()

    print("="*80)
    print("MODELOS DISPONIVEIS:")
    print("="*80)

    for model in models:
        print(f"\nNome: {model.name}")
        print(f"  Display Name: {model.display_name}")
        print(f"  Descrição: {model.description[:100] if model.description else 'N/A'}...")
        print(f"  Métodos suportados: {model.supported_generation_methods}")

    print("\n" + "="*80)
    print("MODELOS RECOMENDADOS PARA generateContent:")
    print("="*80)

    for model in models:
        if 'generateContent' in model.supported_generation_methods:
            print(f"  - {model.name}")

except Exception as e:
    print(f"ERRO ao listar modelos: {e}")
    import traceback
    traceback.print_exc()
