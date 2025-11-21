from graphs.main_graph import build_graph  # Importa a função que constrói o grafo principal do pipeline

def main(): 
    print("\n🎬 Bem-vindo ao CortAI!\n")  # Mensagem inicial de boas-vindas
    
    url_video = input("Insira a URL do Youtube: ").strip()  
    # Solicita ao usuário a URL do vídeo do YouTube e remove espaços extras

    graph = build_graph()  
    # Constrói o grafo de execução do LangGraph (pipeline completo do sistema)

    print(f"\nInicializando o CortAI para: {url_video}")  
    # Informa ao usuário qual URL está sendo processada

    result = graph.invoke({"url": url_video})  
    # Executa o grafo passando o estado inicial contendo a URL do vídeo
    # O LangGraph retornará um dicionário com o estado final (transcrição, análise, highlight etc.)

    print("\n-------------- EXECUÇÃO FINALIZADA --------------")  
    # Marca visualmente o fim do pipeline

    status_transcricao = "OK" if result.get("transcription") else "ERRO"  
    # Verifica se o campo "transcription" existe e não está vazio no estado final

    print(f"\nTranscrição: {status_transcricao}")  
    # Mostra se a etapa de transcrição funcionou

    caminho_final = result.get("highlight_path")  
    # Obtém o caminho final do vídeo editado gerado pelo pipeline

    print(f"Highlight salvo em: {caminho_final}")  
    # Exibe onde o arquivo final foi salvo

# --------------------------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":  
    main()  
    # Se o script for executado diretamente, chama a função principal
