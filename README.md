# JARVIS — Your Personal Local AI Assistant

A private, offline-first AI assistant for Windows that actually *does* things — not just chats. Runs entirely on your own PC using [Ollama](https://ollama.com), so nothing you say ever leaves your machine (except the handful of features that explicitly need the internet, like weather and news).

## Why local?

- **Privacy** — your conversations, files, and habits stay on your PC
- **No subscription** — no API costs, no rate limits, no account required
- **Full control** — every feature is plain, readable Python you can inspect and change

## Features

**Conversation**
- Natural chat, math solving (exact, via SymPy), code writing/explaining
- Persistent voice mode — say "voice mode" for a real back-and-forth conversation; "text mode" to switch back to typing
- Long-term memory — `remember` facts, or `index my notes` from your own files, and `recall` them later (RAG-based, grounded, won't invent answers)
- Full conversation history, auto-pruned after 30 days (moved to Recycle Bin, never permanently deleted)

**System control**
- Open, install, or uninstall almost any app by name (auto-discovers via Windows Start Menu + winget)
- Create, open, organize, or safely delete files/folders (Recycle Bin, never permanent)
- Shutdown, restart, sleep, screen splitting, Bluetooth settings, mute/volume control

**Live information (grounded in real data, not guesses)**
- Real weather (Open-Meteo)
- Real news headlines (RSS, no hallucinated stories)
- Real country facts (REST Countries API)
- Approximate location (IP-based)

**System monitoring**
- Battery, CPU, RAM, GPU, storage, live network speed
- Antivirus/firewall status and threat history (Windows Defender)

**Media**
- Play music from local files, Spotify, or YouTube Music

**Two ways to run it**
- `main.py` — terminal version
- `gui.py` — full dashboard (chat + live system stats + quick controls)

## Tech stack

| Piece | What it does |
|---|---|
| [Ollama](https://ollama.com) | Local LLM inference (Llama 3.1, Qwen2.5-Coder) |
| [Whisper](https://github.com/openai/whisper) (faster-whisper) | Speech-to-text, GPU-accelerated |
| [Piper](https://github.com/rhasspy/piper) | Text-to-speech |
| [ChromaDB](https://www.trychroma.com/) | Local vector memory for RAG |
| SymPy | Exact math |
| psutil, pycaw, winget, PowerShell | System/hardware control |

## Setup

### 1. Install Ollama and pull the models
```bash
ollama pull llama3.1:8b
ollama pull qwen2.5-coder
ollama pull nomic-embed-text
```

### 2. Install Python dependencies
```bash
pip install -r requirements.txt
```
(Some features — voice, Spotify, screen splitting, mic/speaker control, safe delete — have their own optional packages listed as comments in `requirements.txt`.)

### 3. Run it
```bash
python main.py     # terminal version
python gui.py       # dashboard version
```

## Project structure

```
jarvis_assistant/
├── main.py            # terminal entry point + command routing
├── gui.py             # dashboard entry point
├── config.py           # settings — personality, models, folders
├── llm.py               # talks to Ollama
├── voice.py              # speech-to-text / text-to-speech
├── math_tools.py           # exact math via SymPy
├── files_tool.py             # create/open/delete/organize files
├── system_tool.py              # app install/uninstall/open, shutdown, etc.
├── device_tool.py                # battery/CPU/RAM/GPU/network/storage
├── security_tool.py                # antivirus/firewall status
├── music_tool.py                     # local/Spotify/YouTube Music playback
├── bluetooth_tool.py                   # Bluetooth settings/devices
├── screen_tool.py                        # window snapping/split screen
├── weather_tool.py                         # real weather (Open-Meteo)
├── news_tool.py                              # real news (RSS)
├── country_tool.py                             # real country facts
├── location_tool.py                              # IP-based location
├── audio_tool.py                                   # mic/speaker mute, volume
├── rag_tool.py                                       # remember/recall memory
├── chat_log_tool.py                                    # conversation history
└── requirements.txt
```

## Notes on privacy

Everything runs locally except: weather, news, country facts, and location lookups, which need the internet to fetch real (non-hallucinated) data from free public APIs. No conversation data, files, or personal information is ever sent anywhere else.

## License

Personal project — use, modify, and learn from freely.

An example-
<img width="998" height="686" alt="image" src="https://github.com/user-attachments/assets/7b5a7040-25ba-485b-8096-bb6277045d77" />

