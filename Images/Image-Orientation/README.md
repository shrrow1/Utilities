pip install -r requirements.txt

brew install ollama
brew install --cask ollama-binary
OLLAMA_MODELS=/Users/stu/Documents/OllamaLLMs OLLAMA_HOST=127.0.0.1:11434 OLLAMA_NO_CLOUD=1 OLLAMA_FLASH_ATTENTION="1" OLLAMA_KV_CACHE_TYPE="q8_0" /home/linuxbrew/.linuxbrew/opt/ollama/bin/ollama serve
ollama run qwen3-vl:2b ""
ollama ps