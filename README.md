# Ollama-MCP-Streamable-http-Client
A streamable http client for MCP in Python


install Ollama 0.12.3 (https://ollama.com/download/windows)
pull the model : ollama pull qwen3-coder:30b

pip install uv
upgrade pip using : python -m pip install --upgrade pip (pip 25.2)

server:

create virtual environment : uv venv
.venv\Scripts\activate  (for MAC OS or Linux => source ./.venv/bin/activate)
uv pip install -e . 
(if using vscode, probably have to select the python interpreter to resolve the import statements)

uv run src\server.py

client:

uv run src\client.py "Goto MDN and print HTML DOM API page content"

