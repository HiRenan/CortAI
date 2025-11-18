# 📘 CortAI — Agente Transcritor & Agente Analista

Este repositório contém dois módulos principais do sistema **CortAI**, responsáveis por:

- **Agente Transcritor**: baixa vídeos do YouTube, extrai áudio e gera transcrições automáticas usando IA (Whisper).
- **Agente Analista**: processa a transcrição, identifica momentos relevantes e gera insights estruturados utilizando o modelo Gemini via Google GenAI SDK.

Esses dois agentes compõem a primeira etapa do pipeline do nosso **Agente de Mídia Inteligente**.

---

# 🧠 Arquitetura dos Módulos

```
agents/
├── transcriber.py      # Baixa o vídeo e gera a transcrição
└── analyst.py          # Analisa a transcrição e identifica momentos relevantes
```

---

# 🎧 Agente Transcritor (Whisper + yt-dlp)

O Agente Transcritor é responsável por:

- Baixar vídeos do YouTube usando `yt-dlp`
- Extrair o áudio e gerar transcrição com Whisper
- Retornar os trechos com timestamps
- Salvar arquivos `.json` e `.txt` para uso posterior no pipeline

## Funcionalidades

- Download do vídeo com `yt-dlp`
- Conversão do vídeo em áudio pelo FFmpeg
- Transcrição usando Whisper (OpenAI)
- Exportação dos arquivos de transcrição

## Estrutura

```
agents/
└── transcriber.py
```

## Instalação das dependências

Crie e ative o ambiente virtual:

```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/macOS
```

Instale os pacotes:

```bash
pip install -r requirements.txt
```

---

# 🔧 Instalação do FFmpeg

O FFmpeg é necessário para o funcionamento do Whisper e para o processamento de áudio.

## Windows

1. Baixe o FFmpeg: https://ffmpeg.org/download.html  
2. Extraia o ZIP.  
3. Aponte o caminho no `.env`:

```ini
FFMPEG_PATH=C:/Seu/Caminho/ffmpeg/bin/ffmpeg.exe
```

4. (Opcional) Adicione o caminho ao PATH do Windows.

## Linux (Ubuntu/Debian)

```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

## macOS

```bash
brew install ffmpeg
```

---

# 🔐 Configuração do `.env`

Crie um `.env` baseado no `.env.example`:

```ini
FFMPEG_PATH=/caminho/para/ffmpeg.exe
GEMINI_API_KEY=sua_chave_aqui
```

---

# ▶️ Uso do Agente Transcritor

Execute:

```bash
python agents/transcriber.py
```

---

# 🔎 Agente Analista (Gemini 2.0 + Google GenAI SDK)

O Agente Analista recebe o arquivo de transcrição gerado pelo transcritor e realiza:

- Leitura e processamento da transcrição  
- Identificação de **momentos relevantes** (com base em emoção, contexto, ações, picos de conversa e eventos importantes)  
- Geração de insights estruturados em JSON  
- Detecção de highlights para corte  
- Interpretação contextual do vídeo a partir do texto  
- Priorização dos melhores trechos para edição  

## Funcionalidades

- Processamento do arquivo `.json` da transcrição
- Classificação de segmentos relevantes
- Análise semântica usando **Gemini 2.0**
- Suporte a prompts avançados para refinamento
- Geração de saída para o agente editor

## Estrutura

```
agents/
└── analyst.py
```

## Exemplos de Saída

```json
{
  "highlights": [
    {
      "start": "00:02:11",
      "end": "00:02:34",
      "reason": "Pico emocional e reação inesperada do streamer"
    },
    {
      "start": "00:05:40",
      "end": "00:06:10",
      "reason": "Momento de gameplay decisivo"
    }
  ]
}
```

---

# ▶️ Uso do Agente Analista

```bash
python agents/analyst.py
```

O script solicitará:

- Caminho para o arquivo `.json` da transcrição  
- Número de highlights desejados  
- Tipo de conteúdo (gameplay, podcast, vlog, entrevista etc.)

---

# 📦 requirements.txt (versão recomendada)

```txt
yt-dlp
openai-whisper
torch>=1.10.0
python-dotenv==1.0.0
google-genai
```

---

# 📝 Observações Importantes

- O arquivo `.env` **não deve ser versionado** (adicione ao `.gitignore`).
- Apenas `.env.example` deve estar no repositório.
- FFmpeg é uma dependência externa do sistema operacional.

---
