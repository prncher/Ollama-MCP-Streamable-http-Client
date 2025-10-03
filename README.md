# 🧠 MCP Streamable HTTP Client & Server with Ollama and Selenium

This project demonstrates how to build a **Model Context Protocol (MCP)** system using:

- 🧰 **MCP Server** for tool execution  
- 🌐 **Streamable HTTP MCP Client** (Python)  
- 🦙 **Ollama** running `qwen2.5-coder:7b` for reasoning  
- 🖥️ **Selenium** for browser automation

The architecture enables natural language instructions like:

> “Go to MDN and print HTML DOM API page content.”

The **MCP Client** uses Ollama to generate a structured plan of actions and parameters.  
The **MCP Server** executes the plan in a live Selenium browser and streams results back in real time.

## 🧰 Getting Started

### 1. Install Ollama
Download and install **Ollama 0.12.3** from the official site:  
👉 [https://ollama.com/download/windows](https://ollama.com/download/windows)

### 2. Pull the Model
After installing Ollama, pull the required model:

```bash
ollama pull qwen3-coder:30b
```

> 💡 You can also use `qwen2.5-coder:7b` for a faster, lightweight setup.

### 3. Install Python Dependencies
Install [**uv**](https://github.com/astral-sh/uv) (a fast Python package installer):

```bash
pip install uv
```

### 4. Create and Activate a Virtual Environment

#### 🪟 **Windows**
```bash
uv venv
.venv\Scripts\activate
```

#### 🍎 **macOS / 🐧 Linux**
```bash
uv venv
source .venv/bin/activate
```

### 5. Install the Project in Editable Mode
This installs dependencies and links the local project for development:

```bash
uv pip install -e .
```

> 📝 **VS Code Tip**: You may need to manually select the `.venv` Python interpreter to resolve imports.

### 6. Run the MCP Server
Start the MCP server to handle tool execution:

```bash
uv run src\server.py
```

### 7. Run the MCP Client
In a separate terminal, run the MCP Client with a natural language instruction:

```bash
uv run src\client.py "Goto MDN and print HTML DOM API page content"
```

The client will:
- Send the prompt to Ollama
- Receive the action plan
- Forward it to the MCP server
- Stream the results back in real time


## 🧭 Key Features

- **First-of-its-kind Streamable HTTP MCP Client in Python**  
- Real-time streaming of execution logs and results  
- Clean separation of reasoning (LLM) and execution (MCP Server)  
- Extensible toolbox of browser actions (launch, click, scroll, extract, etc.)

## 🏗️ Architecture

```
User → MCP Client → Ollama → MCP Client → MCP Server → Selenium
                         ↑                   ↓
                       Streamed responses ←───
```

📌 See the full article in [`mcp_streamable_http_article.md`](./mcp_streamable_http_article.md) for a deep dive.

## 📝 Tools Implemented

1. Launch Browser  
2. Click Element / Selector  
3. Type Text  
4. Scroll Page  
5. Get Page Content  
6. Get DOM Structure  
7. Take Screenshot  
8. Extract Data  
9. Close Browser

## 🚀 Example

```
Prompt: "Go to MDN and print HTML DOM API page content"
```

The client generates a plan via Ollama, sends it to the server, and streams back the full DOM contents in real time.

## 📂 Repositories

- [MCP Server](https://github.com/prncher/Ollama-MCP-Streamable-http-Server)
- [MCP Client](https://github.com/prncher/Ollama-MCP-Streamable-http-Client)

---

## 🧪 Future Work

- Testing with larger models (`qwen2.5-coder:30b`) to improve selector accuracy  
- Adding persistent event storage for replay and durability  
- Expanding the toolbox with more advanced browser actions

---

## 📄 License

MIT License © 2025
