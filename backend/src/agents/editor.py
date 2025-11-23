import os # Interage com Sistema Operacional
import subprocess # Executa outros programas/comandos do SO
import json # Faz a leitura/escrita em objetos do tipo JSON

# --------------------------------------------------------------------------------------------------------------------------------------

def cortar_video_ffmpeg(input_video, inicio, fim, output_video="data/highlight.mp4", remover_original=False, subtitle_file=None):
    """
    Corta um vídeo entre os timestamps especificados usando FFmpeg.

    Args:
        input_video(str) - Caminho para o vídeo original a ser cortado
        inicio (float) - Timestamp de início do corte em segundos
        fim (float) - Timestamp de fim do corte em segundos
        output_video (str) - Caminho onde o vídeo cortado será salvo
        remover_original(bool) - Se True, remove o vídeo original após o corte
        subtitle_file (str | None) - Caminho para arquivo SRT com legendas burned-in (opcional)

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

    # Import subtitle style function
    from src.agents.screenwriter import get_subtitle_style_youtube

    # Monta o comando FFmpeg para corte eficiente:
    comando = [
        "ffmpeg",
        "-y",                          # Sobrescreve arquivo de saída sem perguntar
        "-ss", str(inicio),            # Posiciona no timestamp de início (seek rápido)
        "-i", input_video,             # Especifica arquivo de entrada
        "-t", str(duracao),            # Define quanto tempo cortar a partir do início
    ]

    # Se legendas foram fornecidas, adiciona filtro de subtitles burned-in
    if subtitle_file and os.path.exists(subtitle_file):
        # Normaliza o caminho para funcionar com FFmpeg (Windows paths)
        subtitle_path_normalized = subtitle_file.replace("\\", "/").replace(":", r"\:")
        style = get_subtitle_style_youtube()
        vf_filter = f"subtitles='{subtitle_path_normalized}':force_style='{style}'"

        comando.extend([
            "-vf", vf_filter,          # Aplica filtro de legendas
            "-c:v", "libx264",         # Reencode vídeo (necessário para filtros)
            "-preset", "veryfast",
            "-crf", "23",
        ])
    else:
        comando.extend([
            "-c:v", "libx264",         # Reencode para garantir sync de áudio/vídeo
            "-preset", "veryfast",
            "-crf", "23",
        ])

    comando.extend([
        "-c:a", "aac",
        "-movflags", "+faststart",
        output_video
    ])

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

def _normalize_highlights(dados):
    """Normaliza diferentes formatos de highlight para uma lista uniforme.

    Aceita:
    - {"highlights": [...]} (novo formato)
    - lista direta de highlights
    - dict único com chaves start/end ou highlight_inicio_segundos/highlight_fim_segundos
    """

    if isinstance(dados, dict) and "highlights" in dados:
        return dados["highlights"]

    if isinstance(dados, list):
        return dados

    if isinstance(dados, dict):
        start = dados.get("start", dados.get("highlight_inicio_segundos", dados.get("inicio")))
        end = dados.get("end", dados.get("highlight_fim_segundos", dados.get("fim")))

        # Garante que start/end existam
        if start is None or end is None:
            raise ValueError("ERRO: JSON de highlight não contém campos de início/fim válidos")

        return [{
            "start": float(start),
            "end": float(end),
            "summary": dados.get("summary") or dados.get("resumo") or dados.get("resposta_bruta", ""),
            "score": dados.get("score") or dados.get("pontuacao", 0),
        }]

    raise ValueError("ERRO: Formato do JSON inválido. Esperado lista ou chave 'highlights'.")


def executar_agente_editor(
    highlight_json="data/highlight.json",
    input_video="data/temp_video.mp4",
    output_dir="data/clips",
    output_video=None,
    transcription_path=None,
    include_subtitles=True,
):
    """
    Orquestra o processo completo de edição: lê os highlights do JSON e gera múltiplos clips.

    IMPORTANTE: Esta versão processa múltiplos highlights (não apenas um).
    Cada highlight gera um arquivo .mp4 separado.

    Args:
        highlight_json(str) - Caminho para o arquivo JSON com a lista de highlights
        input_video (str) - Caminho para o vídeo original a ser editado
        output_dir (str) - Diretório onde os clips serão salvos (default: data/clips)
        output_video (str | None) - Caminho explícito para o output quando há apenas 1 highlight (compatibilidade)
        transcription_path (str | None) - Caminho para o arquivo de transcrição (necessário para legendas)
        include_subtitles (bool) - Se True, adiciona legendas burned-in nos clips (default: True)

    Returns:
        list[str] ou str - Lista com os caminhos de todos os clips gerados
        (ou caminho único se apenas um highlight for processado)

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
    highlights = _normalize_highlights(dados)

    if not highlights:
        raise ValueError("ERRO: Nenhum highlight encontrado no JSON")

    # Garante que o diretório de saída existe
    os.makedirs(output_dir, exist_ok=True)

    single_output_path = output_video if output_video and len(highlights) == 1 else None
    if single_output_path:
        os.makedirs(os.path.dirname(single_output_path), exist_ok=True)

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
                print(f"  [AVISO] Highlight {idx} ignorado: timestamps inválidos ({inicio}s >= {fim}s)")
                continue

            # Gera nome do arquivo de saída
            duracao = fim - inicio
            suffix = "_with_subs" if include_subtitles else ""
            output_filename = f"clip_{idx:02d}_inicio_{int(inicio)}s_duracao_{int(duracao)}s{suffix}.mp4"
            output_path = single_output_path or os.path.join(output_dir, output_filename)

            print(f"\n  Highlight {idx}/{len(highlights)}:")
            print(f"    Início: {inicio:.1f}s | Fim: {fim:.1f}s | Duração: {duracao:.1f}s")
            if score:
                print(f"    Score: {score}")
            if summary:
                print(f"    Resumo: {summary[:80]}{'...' if len(summary) > 80 else ''}")

            # Gera legendas temporárias se necessário
            subtitle_file = None
            if include_subtitles and transcription_path and os.path.exists(transcription_path):
                try:
                    from src.agents.screenwriter import make_srt
                    from src.core.graph import build_clipped_transcription

                    # Cria transcrição ajustada para este clip
                    clipped_transcription = build_clipped_transcription(
                        transcription_path,
                        start=inicio,
                        end=fim
                    )

                    # Gera arquivo SRT temporário
                    temp_srt_path = os.path.join(output_dir, f"temp_clip_{idx:02d}.srt")
                    make_srt(clipped_transcription, temp_srt_path)
                    subtitle_file = temp_srt_path
                    print(f"    ℹ Legendas geradas: {os.path.basename(temp_srt_path)}")
                except Exception as e:
                    print(f"    [AVISO] Não foi possível gerar legendas: {e}")

            # Corta o vídeo (com ou sem legendas)
            clip_path = cortar_video_ffmpeg(
                input_video=input_video,
                inicio=inicio,
                fim=fim,
                output_video=output_path,
                remover_original=False,
                subtitle_file=subtitle_file
            )

            # Remove arquivo SRT temporário após processamento
            if subtitle_file and os.path.exists(subtitle_file):
                try:
                    os.remove(subtitle_file)
                except Exception:
                    pass

            generated_clips.append(clip_path)
            status_msg = "COM legendas" if include_subtitles else "SEM legendas"
            print(f"    ✓ Clip gerado {status_msg}: {output_filename}")

        except Exception as e:
            print(f"  [ERRO] Falha ao processar highlight {idx}: {str(e)}")
            continue

    print("")
    print("-"*50)
    print(f"✓ Edição concluída: {len(generated_clips)}/{len(highlights)} clips gerados")
    print("-"*50)

    if not generated_clips:
        raise RuntimeError("ERRO: Nenhum clip foi gerado com sucesso")

    # Retorna lista de caminhos (ou único caminho para compatibilidade)
    if len(generated_clips) == 1:
        return generated_clips[0]
    return generated_clips

# --------------------------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":

    # Executa o agente editor 
    caminho_highlight = executar_agente_editor()
    
    # Exibe o resultado final para confirmação visual
    print("")
    print(f"Pipeline de edição concluído: {caminho_highlight}")
    print("-"*50)

