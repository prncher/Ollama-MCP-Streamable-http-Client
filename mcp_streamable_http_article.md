![Title Image](https://raw.githubusercontent.com/prncher/Ollama-MCP-Streamable-http-Server/main/TitleImage.png)

# Building an MCP System with Streamable HTTP, Ollama, and Selenium

The **Model Context Protocol (MCP)** is designed to let large language models (LLMs) interact with external tools in a structured way. In this article, I’ll describe how I built an MCP Client and MCP Server that communicate over **streamable HTTP**, where the client uses **Ollama running `qwen2.5-coder:7b`** for reasoning, and the server executes actions using **Selenium browser automation**.

This architecture allows a user to give natural language instructions like:

> “Go to MDN and print HTML DOM API page content.”

The system then:  
1. **Analyzes** the request with Ollama.  
2. **Generates tool actions** and parameters.  
3. **Executes those actions** in a live Selenium browser.  
4. **Streams results back** to the user in real time.  

---

## Architecture Overview

Here’s how the components fit together:

1. **User → MCP Client**  
   The user sends a natural language request.  

2. **MCP Client ⇄ Ollama**  
   The client queries Ollama (`qwen2.5-coder:7b`) to transform the request into structured actions and parameters.  

3. **MCP Client → MCP Server**  
   The client sends Ollama’s output as an HTTP POST request.  

4. **MCP Server → Selenium**  
   The server interprets the plan and executes the tools inside a Selenium browser session.  

5. **MCP Server → MCP Client**  
   The server streams logs, partial results, and final outputs back to the client in real time.  

<img width="1536" height="1024" alt="image" src="https://raw.githubusercontent.com/prncher/Ollama-MCP-Streamable-http-Server/main/496902944-f4e132f4-9e7f-4d79-a057-b8dc0138b263.png" />

---

## MCP Client

The MCP Client plays the role of **mediator**:

- It handles user prompts.  
- It queries Ollama for reasoning.  
- It POSTs Ollama’s action plan to the MCP Server.  
- It listens to streaming events from the server and displays progress/results.  

### Why This Client is Novel
Most MCP client examples, such as those in the [official MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk), are built around **standard request/response models**.

Based on my research, this project may be the **first working Streamable HTTP MCP Client in Python**.

Unlike traditional clients, this one:  
- **Streams live events** from the MCP Server.  
- Allows incremental responses instead of waiting for a full run to complete.  
- Enables **interactive automation workflows**, making the client an active participant in the process.  

👉 Code: [MCP Client GitHub repo](https://github.com/prncher/Ollama-MCP-Streamable-http-Client)  

---

## MCP Server

The MCP Server is the **executor**. It receives plans from the client, interprets them, and performs browser automation using **Selenium**.

- The server exposes a **set of tools** that can be invoked by the client.  
- Each tool is parameterized — Ollama provides the parameters when generating the plan.  
- Results and logs are **streamed back** through an HTTP session.  

👉 Code: [MCP Server GitHub repo](https://github.com/prncher/Ollama-MCP-Streamable-http-Server/blob/main/src/server.py)  

---

## Tools Exposed by the MCP Server

The server provides a **toolbox of browser actions**. These tools are the building blocks Ollama can call:

1. **Launch Browser** – start a Selenium session.  
2. **Click Element** – click an element by selector.  
3. **Click Selector** – shorthand for CSS clicks.  
4. **Type Text** – enter text into input fields.  
5. **Scroll Page** – scroll by offset or to element.  
6. **Get Page Content** – return raw HTML.  
7. **Get DOM Structure** – return structured DOM representation.  
8. **Take Screenshot** – capture viewport.  
9. **Extract Data** – extract attributes/text.  
10. **Close Browser** – end the session.  

Parameters are included in Ollama’s output. Example:

```json
{ "action": "Type Text", "params": { "selector": "#search", "text": "JavaScript DOM" } }
```

---

## Example Walkthrough: MDN DOM API

User prompt:

> “Go to MDN and print HTML DOM API page content.”

1. **Client → Ollama:**  
   User input is sent to Ollama (`qwen2.5-coder:7b`).  

2. **Ollama → Client:**  
   Returns an action plan:  
   ```json
   [
     { "action": "Launch Browser", "params": { "headless": true } },
     { "action": "navigate", "url": "https://developer.mozilla.org/en-US/docs/Web/API/Document_Object_Model" },
     { "action": "Get Page Content" },
     { "action": "Close Browser" }
   ]
   ```  

3. **Client → MCP Server:**  
   Forwards the plan via HTTP POST.  

4. **MCP Server → Client:**  
   Streams progress and results back:  
   ```json
   { "event": "log", "message": "Launching headless browser..." }
   { "event": "log", "message": "Navigating to MDN DOM API..." }
   { "event": "result", "content": "<!DOCTYPE html> ... full DOM ..." }
   { "event": "log", "message": "Closing browser." }
   ```  

---

## Selector Challenges

One limitation is that Ollama sometimes generates **incorrect selectors**:

- It may suggest `#main-content` when the page actually uses `.main`.  
- It may try to click `#login-btn` when the real element is `button[type=submit]`.  

This happens because the LLM cannot fully “see” the DOM structure before execution.  

### Error-Handling Strategies

To mitigate this, the MCP Server can:  
1. **Validate selectors** before execution and return structured errors.  
2. **Provide fallbacks** using alternate locator strategies.  
3. **Return DOM context** snippets to Ollama for correction.  
4. **Support iterative correction loops** where Ollama re-plans after errors.  

---

## Practical Considerations

### A First-of-Its-Kind Streamable HTTP MCP Client in Python
Based on my research — including the [official MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) and related articles — there appear to be **no existing MCP clients in Python that support streamable HTTP**.

This project may therefore be the **first working implementation** of such a client. It demonstrates that Python can be used to build **reactive MCP applications** with incremental streaming.

### Browser Automation Choice
I initially experimented with **Playwright**, but integration challenges made it hard to align with streaming requirements. **Selenium**, despite quirks, proved more practical for this prototype.

### Streaming Session Management
The `StreamableHTTPSessionManager` in the MCP Server streams events directly to the client.

- No **persistent event store** is currently used.  
- This keeps the design simple and focused.  
- Future versions could add durability and replay features, but for now, direct streaming is sufficient.  

---

# Conclusion

This project shows how MCP can be combined with **Ollama** and **Selenium** into a working system:

- **Client**: first-of-its-kind Streamable HTTP MCP client in Python.  
- **Server**: browser automation tools via Selenium.  
- **LLM**: Ollama (`qwen2.5-coder:7b`) generating structured action plans.  

By separating **reasoning** (Ollama) from **execution** (MCP Server tools), the system achieves transparent, extendable, and interactive automation.
