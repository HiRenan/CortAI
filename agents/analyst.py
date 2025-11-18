import os # Interage com o Sistema Operacional
import json # Faz a leitura/escrita em objetos do tipo JSON
import re # Expressões Regulares
from dotenv import load_dotenv # Acessa as variáveis de ambiente 
from google import genai # Acessa o modelo de linguagem do Google (Gemini)

# Acessa as variáveis de ambiente e obtem a chave da api do Gemini
load_dotenv()
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")

# Caso a chave não seja encontrada, retorna a mensagem de erro
if not GEMINI_API_KEY:
    raise ValueError("ERRO: variável GOOGLE_API_KEY não encontrada no .env!")

# Faz a inicialização e validação do cliente Gemini
client = genai.Client(api_key=GEMINI_API_KEY)

# --------------------------------------------------------------------------------------------------------------------------------------

def normalizar_timestamp(ts):
    """
    Normaliza timestamps para o formato padrão HH:MM:SS.

    Args:
        ts(str) - Timestamp no formato HH:MM:SS ou MM:SS

    Returns:
        str - Timestamp normalizado no formato HH:MM:SS
    """

    # Divide a string do timestamp usando ':' como delimitador
    # Exemplo: "05:30" → ["05", "30"] ou "1:23:45" → ["1", "23", "45"]
    partes = ts.split(":")
    
    # Se o timestamp tem apenas 2 partes (formato MM:SS), adiciona "00" no início para representar as horas
    # Exemplo: ["05", "30"] → ["00", "05", "30"]
    if len(partes) == 2:
        partes = ["00"] + partes

    # Converte cada parte para inteiro usando map() e desempacota nas variáveis h, m, s
    # Exemplo: ["00", "05", "30"] → h=0, m=5, s=30
    h, m, s = map(int, partes)

    # Formata cada componente com 2 dígitos e junta com ':'
    # Exemplo: 0, 5, 30 → "00:05:30"
    return f"{h:02d}:{m:02d}:{s:02d}"

# --------------------------------------------------------------------------------------------------------------------------------------

def converter_timestamp(timestamp):
    """
    Converte timestamp no formato HH:MM:SS para segundos totais.

    Args:
        timestamp(str) - Timestamp no formato HH:MM:SS

    Returns:
        int - Total de segundos representado pelo timestamp
    """
    # Divide o timestamp e converte cada componente para segundos
    horas, minutos, segundos = timestamp.split(":")

    # Retorna o total de tempo em segundos somado
    return int(horas) * 3600 + int(minutos) * 60 + int(segundos)

# --------------------------------------------------------------------------------------------------------------------------------------

def extrair_timestamp(resposta):
    """
    Extrai intervalos de timestamp da resposta do modelo Gemini.

    Args:
        resposta(str) - Texto retornado pelo modelo contendo timestamps

    Returns:
        tuple - Tupla contendo (inicio_segundos, fim_segundos) ou (None, None) em caso de erro
    """

    # Padrão regex que busca por dois timestamps separados por hífen/traço
    padrao = r"(\d{1,2}:\d{1,2}:\d{1,2}|\d{1,2}:\d{1,2})\s*[-–]\s*(\d{1,2}:\d{1,2}:\d{1,2}|\d{1,2}:\d{1,2})"
    
    # Busca por todos os intervalos de tempo encontrados na resposta
    intervalos_encontrados = re.findall(padrao, resposta)

    # Retorna None se nenhum timestamp for encontrado
    if not intervalos_encontrados:
        return None, None

    # Usa o primeiro par de timestamps encontrado na resposta
    inicio_raw, fim_raw = intervalos_encontrados[0]

    # Normaliza os timestamps para formato padrão
    inicio_norm = normalizar_timestamp(inicio_raw)
    fim_norm = normalizar_timestamp(fim_raw)

    # Converte para segundos totais
    inicio_seg = converter_timestamp(inicio_norm)
    fim_seg = converter_timestamp(fim_norm)

    # Garantir que início < fim (intervalo válido)
    if inicio_seg >= fim_seg:
        return None, None

    return inicio_seg, fim_seg

# --------------------------------------------------------------------------------------------------------------------------------------

def executar_agente_analista(input_json="data/transcricao_final.json", output_json="data/highlight.json"):
    """
    Analisa a transcrição de um vídeo e identifica o momento mais relevante usando LLM.

    Args:
        input_json(str) - Caminho para o arquivo JSON com a transcrição
        output_json (str) - Caminho para salvar o resultado com os highlights

    Returns:
        dict - Dicionário contendo os timestamps do highlight e resposta bruta do modelo

    Raises:
        FileNotFoundError - Se o arquivo de transcrição não for encontrado
        ValueError - Se a transcrição estiver vazia ou não contiver timestamps válidos
    """
    
    # Verifica se o arquivo de transcrição existe
    if not os.path.exists(input_json):
        raise FileNotFoundError(f"ERRO: arquivo {input_json} não encontrado!")

    # Carrega o arquivo JSON com a transcrição
    with open(input_json, "r", encoding="utf-8") as f:
        dados_transcricao = json.load(f)

    # Extrai o texto da transcrição do dicionário
    texto_transcricao = dados_transcricao.get("text", "").strip()

    # Valida se a transcrição não está vazia
    if not texto_transcricao:
        raise ValueError("ERRO: O JSON de transcrição não contém campo 'text'!")


    prompt = f"""
                Você é um especialista em análise de conteúdo de vídeo com expertise em identificar momentos-chave e highlights impactantes. 
                Sua missão é analisar transcrições e localizar o trecho mais relevante do conteúdo.

                Analise a transcrição abaixo e identifique o ÚNICO intervalo temporal mais importante, impactante ou relevante do vídeo.

                # CRITÉRIOS DE SELEÇÃO (em ordem de prioridade):
                1. **Trecho mais compartilhável** - parte que teria maior engajamento em redes sociais
                2. **Momento de maior impacto emocional** - pico de emoção, revelação surpreendente ou conclusão poderosa
                3. **Clímax narrativo** - ápice da história, resolução de conflito ou momento decisivo
                4. **Ponto crucial informativo** - informação mais valiosa, insight principal ou aprendizado central
                5. **Resumo natural** - segmento que melhor representa a essência do conteúdo completo

                Você DEVE retornar EXCLUSIVAMENTE no formato: HH:MM:SS - HH:MM:SS

                # REGRAS ESTRITAS:
                - NUNCA inclua explicações, justificativas ou textos adicionais
                - NÃO adicione prefixos como "Resposta:" ou "Timestamp:"
                - NÃO use marcadores, listas ou formatação complexa
                - USE APENAS o formato HH:MM:SS - HH:MM:SS
                - GARANTA que o início seja sempre menor que o fim
                - CONSIDERE intervalos entre 30 segundos e 3 minutos (a menos que o contexto exija diferente)

                # EXEMPLOS VÁLIDOS DE RESPOSTA:
                00:05:30 - 00:07:45
                01:15:00 - 01:17:30
                00:00:00 - 00:02:15

                # EXEMPLOS INVÁLIDOS (NÃO FAÇA):
                "O momento mais importante é 00:05:30 - 00:07:45 porque..."
                00:05:30 - 00:07:45
                Timestamp: 00:05:30-00:07:45

                # TRANSCRIÇÃO PARA ANÁLISE:
                {texto_transcricao}

                # LEMBRETE FINAL:
                Retorne SOMENTE o intervalo no formato HH:MM:SS - HH:MM:SS. Qualquer texto adicional invalidará a resposta.
            """

    # Envia o prompt para o modelo Gemini e obtém a resposta
    resposta = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )

    # Extrai e limpa o texto da resposta
    texto_resposta = resposta.text.strip()

    # Processa a resposta para extrair os timestamps
    inicio, fim = extrair_timestamp(texto_resposta)

    # Valida se os timestamps foram extraídos com sucesso
    if inicio is None or fim is None:
        raise ValueError(f"ERRO: Não foi possível extrair timestamp da resposta: {texto_resposta}")

    # Salvar resultado
    resultado = {
        "resposta_bruta": texto_resposta,
        "highlight_inicio_segundos": inicio,
        "highlight_fim_segundos": fim
    }

    # Salva os resultados em arquivo JSON
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=4)

    return resultado

# --------------------------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":

    # Executa o agente analista com os parâmetros padrão
    resultado = executar_agente_analista("data/transcricao_final.json")

    # Exibe os resultados para o usuário
    print("")
    print("-"*50)
    print("Resposta do modelo:")
    print(resultado["resposta_bruta"])

    print("\nInício (segundos):", resultado["highlight_inicio_segundos"])
    print("Fim (segundos):", resultado["highlight_fim_segundos"])
    print("-"*50)
