import os # Interage com Sistema Operacional
import subprocess # Executa outros programas/comandos do SO
import json # Faz a leitura/escrita em objetos do tipo JSON

# Duração mínima de fallback (segundos) quando um highlight tem fim <= início
DEFAULT_FALLBACK_SECONDS = 5

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

def executar_agente_editor(highlight_json="data/highlight.json", input_video="data/temp_video.mp4", output_dir="data/clips"):
    """
    Orquestra o processo completo de edição: lê os highlights do JSON e gera múltiplos clips.

    IMPORTANTE: Esta versão processa múltiplos highlights (não apenas um).
    Cada highlight gera um arquivo .mp4 separado.

    Args:
        highlight_json(str) - Caminho para o arquivo JSON com a lista de highlights
        input_video (str) - Caminho para o vídeo original a ser editado
        output_dir (str) - Diretório onde os clips serão salvos (default: data/clips)

    Returns:
        list[str] - Lista com os caminhos de todos os clips gerados

    Raises:
        FileNotFoundError - Se o arquivo JSON ou vídeo de entrada não forem encontrados
        ValueError - Se os campos necessários não estiverem no JSON ou forem inválidos
    """

    # Valida se o arquivo JSON com os timestamps existe
    if not os.path.exists(highlight_json):
        raise FileNotFoundError(f"Arquivo não encontrado: {highlight_json}")

    # Carrega e parseia o arquivo JSON com os dados dos highlights
    with open(highlight_json, "r", encoding="utf-8") as f:
        dados = json.load(f)

    # Extrai a lista de highlights
    # Suporta tanto o novo formato {"highlights": [...]} quanto formato direto [...]
    if isinstance(dados, dict) and "highlights" in dados:
        highlights = dados["highlights"]
    elif isinstance(dados, list):
        highlights = dados
    else:
        raise ValueError("ERRO: Formato do JSON inválido. Esperado: {'highlights': [...]}")

    if not highlights or len(highlights) == 0:
        raise ValueError("ERRO: Nenhum highlight encontrado no JSON")

    # Garante que o diretório de saída existe
    os.makedirs(output_dir, exist_ok=True)

    print("")
    print("-"*50)
    print(f"Processando {len(highlights)} highlight(s)...")
    print("-"*50)

    generated_clips = []

    # Processa cada highlight individualmente
    for idx, highlight in enumerate(highlights, 1):
        try:
            # Extrai timestamps (suporta ambos os formatos)
            inicio = float(highlight.get("start", highlight.get("inicio", 0)))
            fim = float(highlight.get("end", highlight.get("fim", 0)))
            summary = highlight.get("summary", highlight.get("resumo", ""))
            score = highlight.get("score", highlight.get("pontuacao", 0))

            if inicio >= fim:
                # Aplica fallback seguro: define fim = inicio + DEFAULT_FALLBACK_SECONDS
                old_inicio, old_fim = inicio, fim
                fim = inicio + DEFAULT_FALLBACK_SECONDS
                print(f"  [AVISO] Highlight {idx} com timestamps inválidos ({old_inicio}s >= {old_fim}s). Aplicando fallback: fim={fim}s (+{DEFAULT_FALLBACK_SECONDS}s).")

            # Gera nome do arquivo de saída
            duracao = fim - inicio
            output_filename = f"clip_{idx:02d}_inicio_{int(inicio)}s_duracao_{int(duracao)}s.mp4"
            output_path = os.path.join(output_dir, output_filename)

            print(f"\n  Highlight {idx}/{len(highlights)}:")
            print(f"    Início: {inicio:.1f}s | Fim: {fim:.1f}s | Duração: {duracao:.1f}s")
            if score:
                print(f"    Score: {score}")
            if summary:
                print(f"    Resumo: {summary[:80]}{'...' if len(summary) > 80 else ''}")

            # Corta o vídeo
            clip_path = cortar_video_ffmpeg(
                input_video=input_video,
                inicio=inicio,
                fim=fim,
                output_video=output_path,
                remover_original=False
            )

            generated_clips.append(clip_path)
            print(f"    ✓ Clip gerado: {output_filename}")

        except Exception as e:
            print(f"  [ERRO] Falha ao processar highlight {idx}: {str(e)}")
            continue

    print("")
    print("-"*50)
    print(f"✓ Edição concluída: {len(generated_clips)}/{len(highlights)} clips gerados")
    print("-"*50)

    if not generated_clips:
        raise RuntimeError("ERRO: Nenhum clip foi gerado com sucesso")

    # Retorna lista de caminhos dos clips gerados
    return generated_clips

# --------------------------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":

    # Executa o agente editor 
    caminho_highlight = executar_agente_editor()
    
    # Exibe o resultado final para confirmação visual
    print("")
    print(f"Pipeline de edição concluído: {caminho_highlight}")
    print("-"*50)

