# Agente Transcritor CortAI

Este módulo implementa o agente responsável por baixar vídeos do YouTube e gerar transcrições automáticas de áudio usando IA (Whisper).

## Funcionalidades

- Download de vídeos do YouTube através da ferramenta `yt-dlp`.
- Extração e transcrição do áudio do vídeo com o modelo Whisper (OpenAI).
- Todas as informações temporais (início/duração dos trechos) disponíveis para pós-processamento.

## Estrutura

```
agents/
└── transcriber.py
```

## Instalação das dependências

Crie e ative o ambiente virtual:

```bash
python -m venv venv # Windows/Linux/macOS
venv\Scripts\activate # Windows
source venv/bin/activate # Linux/macOS
```

Instale os pacotes Python:

```bash
pip install -r requirements.txt
```

## Instalação do ffmpeg

O `ffmpeg` é necessário tanto para Whisper quanto para tratamento de vídeo/áudio.
Ele **NÃO** é instalado por `pip`. Siga as instruções conforme o seu sistema:

### Windows

1. Baixe o ffmpeg em: [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)
2. Extraia o arquivo ZIP.
3. Coloque o caminho para o executável `ffmpeg.exe` no `.env` do projeto:

```ini
FFMPEG_PATH=C:/Seu/Path/ffmpeg/bin/ffmpeg.exe
```

4. Opcional: Adicione a pasta `bin` do ffmpeg no PATH do Windows para uso por linha de comando.

### Linux (Debian/Ubuntu)

```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

### macOS

```bash
brew install ffmpeg
```

## Configuração do .env

Crie um arquivo `.env` (com base no `.env.example`) contendo o caminho do ffmpeg:

```ini
FFMPEG_PATH=/caminho/completo/ffmpeg.exe
```

## Uso Básico

No diretório do projeto, execute:

```bash
python agents/transcriber.py
```

Siga as instruções para inserir a URL do vídeo desejado.

## Observações

- O arquivo `.env` não deve ser versionado. Compartilhe apenas o `.env.example`.
- Para colaborar basta instalar as dependências, ffmpeg e preencher o .env localmente.

---
