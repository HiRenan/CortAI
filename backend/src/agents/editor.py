import os # Interage com Sistema Operacional
import subprocess # Executa outros programas/comandos do SO
import json # Faz a leitura/escrita em objetos do tipo JSON

# --------------------------------------------------------------------------------------------------------------------------------------

def cortar_video_ffmpeg(input_video, inicio, fim, output_video="data/highlight.mp4", remover_original=False):
    """
    Corta um vídeo entre os timestamps especificados usando FFmpeg.

    Args:
        input_video(str) - Caminho para o vídeo original a ser cortado
        inicio (float) - Timestamp de início do corte em segundos
        fim (float) - Timestamp de fim do corte em segundos  
        output_video (str) - Caminho onde o vídeo cortado será salvo
        remover_original(bool) - Se True, remove o vídeo original após o corte

    Returns:
        str - Caminho do arquivo de vídeo gerado (highlight)

    Raises:
        FileNotFoundError - Se o vídeo de entrada não for encontrado
        ValueError - Se os timestamps formarem uma duração inválida
        RuntimeError - Se o FFmpeg falhar durante o processamento
    """

    # Verifica se o arquivo de vídeo de entrada existe no sistema
    if not os.path.exists(input_video):
        raise FileNotFoundError(f"ERRO: Vídeo de entrada não encontrado: {input_video}")

    # Calcula a duração do corte e valida se é positiva
    duracao = fim - inicio
    if duracao <= 0:
        raise ValueError("ERRO: O valor de fim deve ser maior que o início.")

    # Garante que o diretório de saída exista (cria se necessário)
    os.makedirs(os.path.dirname(output_video), exist_ok=True)

    # Monta o comando FFmpeg para corte eficiente:
    comando = [
        "ffmpeg",
        "-y",                          # Sobrescreve arquivo de saída sem perguntar
        "-ss", str(inicio),            # Posiciona no timestamp de início
        "-i", input_video,             # Especifica arquivo de entrada
        "-t", str(duracao),            # Define quanto tempo cortar a partir do início
        "-c", "copy",                  # Copia os streams sem re-encoding
        output_video
    ]

    # Exibe o comando que será executado para debugging transparente
    print(f"Executando FFmpeg: {comando}")

    # Executa o comando FFmpeg e captura stdout/stderr
    resultado = subprocess.run(
        comando,
        capture_output=True,
        text=True
    )

    # Verifica se o FFmpeg executou com sucesso (returncode 0 = sucesso)
    if resultado.returncode != 0:
        # Exibe a saída de erro do FFmpeg para diagnóstico
        print("Saída do FFmpeg:", resultado.stderr)
        raise RuntimeError("Erro ao cortar vídeo com FFmpeg.")

     # Confirmação de sucesso na geração do highlight
    print(f"Highlight gerado: {output_video}")

    # Remoção do vídeo original (para limpeza de arquivos)
    if remover_original:
        try:
            os.remove(input_video)
            print(f"Vídeo original removido: {input_video}")
        except Exception as e:
            print(f"Aviso: não foi possível remover {input_video}: {e}")

    # Retorna o caminho do arquivo gerado para uso em pipelines
    return output_video

# --------------------------------------------------------------------------------------------------------------------------------------

def executar_agente_editor(highlight_json="data/highlight.json", input_video="data/temp_video.mp4", output_video="data/highlight.mp4"):
    """
    Orquestra o processo completo de edição: lê os timestamps do JSON e corta o vídeo.

    Args:
        highlight_json(str) - Caminho para o arquivo JSON com os timestamps do highlight
        input_video (str) - Caminho para o vídeo original a ser editado
        output_video (str) - Caminho onde o vídeo editado será salvo

    Returns:
        str - Caminho do arquivo de vídeo gerado com o highlight

    Raises:
        FileNotFoundError - Se o arquivo JSON ou vídeo de entrada não forem encontrados
        ValueError - Se os campos necessários não estiverem no JSON ou forem inválidos
    """

    # Valida se o arquivo JSON com os timestamps existe
    if not os.path.exists(highlight_json):
        raise FileNotFoundError(f"Arquivo não encontrado: {highlight_json}")

    # Carrega e parseia o arquivo JSON com os dados do highlight
    with open(highlight_json, "r", encoding="utf-8") as f:
        dados = json.load(f)

    # Extrai os timestamps de início e fim do JSON com tratamento de erro
    # Usa float() para garantir precisão em cálculos com segundos decimais
    try:
        inicio = float(dados["highlight_inicio_segundos"])
        fim = float(dados["highlight_fim_segundos"])
    except KeyError as e:
        # Informa qual campo específico está faltando no JSON
        raise ValueError(f"ERRO: Campo ausente no highlight.json: {e}")

    # Exibe os timestamps que serão usados para transparência do processo
    print("")
    print("-"*50)
    print(f"Início: {inicio}s | Fim: {fim}s")

    # Executa o corte do vídeo usando os timestamps extraídos
    caminho_final = cortar_video_ffmpeg(
        input_video=input_video,
        inicio=inicio,
        fim=fim,
        output_video=output_video,
        remover_original=False  
    )

    # Retorna o caminho do highlight gerado
    return caminho_final

# --------------------------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":

    # Executa o agente editor 
    caminho_highlight = executar_agente_editor()
    
    # Exibe o resultado final para confirmação visual
    print("")
    print(f"Pipeline de edição concluído: {caminho_highlight}")
    print("-"*50)

