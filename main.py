from graphs.main_graph import build_graph# Importa o grafo 

def main(): 
    print("\n🎬 Bem-vindo ao CortAI!\n")
    url_video = input("Insira a URL do Youtube: ").strip()

    # Chama a função que conecta os nós
    graph = build_graph()

    # Inicia o fluxo
    print(f"\nInicializando o CortAI para: {url_video}")

    # Passa o estado inicial e faz a invocação
    result = graph.invoke({"url": url_video})

    print("\n-------------- EXECUÇÃO FINALIZADA --------------")

    # Verifica se a chave transcription foi preenchida no estado
    status_transcricao = "OK" if result.get("transcription") else "ERRO"
    print(f"\nTranscrição: {status_transcricao}")

    # Pega o caminho final do vídeo editado 
    caminho_final = result.get("highlight_path")
    print(f"Highlight salvo em: {caminho_final}")

# --------------------------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    main()