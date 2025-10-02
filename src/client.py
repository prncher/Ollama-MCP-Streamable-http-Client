import argparse
import asyncio
from contextlib import AsyncExitStack
from datetime import timedelta
import json
import logging
import os
from typing import Any, Dict, Optional

from mcp import ClientSession, StdioServerParameters, stdio_client
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from mcp.client.streamable_http import streamablehttp_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ollama-browser-session")

class MCPClient:
    def __init__(self,server_url: str, transport_type: str, initial_task: str):
        self.server_url = server_url
        self.transport_type = transport_type
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.task = initial_task
        
        # Get Ollama model from environment variable or use default
        ollama_model = os.environ.get("OLLAMA_MODEL", "qwen2.5-coder:7b")
        logger.info(f"Using Ollama model: {ollama_model}")
        
        # Configure Ollama with optimized parameters
        self.llm = ChatOllama(
            model=ollama_model,
            num_ctx=32000,  # Large context window for complex tasks
            base_url="http://localhost:11434",
            temperature=0,  # Deterministic outputs for consistent automation
        )
        
        # Initialize conversation history for continuous context
        self.messages:list[SystemMessage|HumanMessage|AIMessage] = [
            SystemMessage(content="""You are an expert browser automation assistant with advanced capabilities for web analysis and data extraction. 
            You will be given access to browser automation tools and will help navigate websites, extract information, and perform tasks.
            You should think step by step, explaining your reasoning, and then decide on the next action to take.
            """)
        ]
        
        # Cache for storing frequently accessed data
        self.cache = {}
    
    async def connect(self):
        """Connect to the MCP server."""
        print(f"🔗 Attempting to connect to {self.server_url}...") 

        print("📡 Opening StreamableHTTP transport connection with auth...")
        async with streamablehttp_client(
            url=self.server_url,
            timeout=timedelta(seconds=60),
        ) as (read_stream, write_stream, get_session_id):
            await self._run_session(read_stream, write_stream, get_session_id)

    async def _run_session(self, read_stream, write_stream, get_session_id):
        """Run the MCP session with the given streams."""
        print("🤝 Initializing MCP session...")
        async with ClientSession(read_stream, write_stream) as session:
            self.session = session
            print("⚡ Starting session initialization...")
            await session.initialize()
            print("✨ Session initialization complete!")

            print(f"\n✅ Connected to MCP server at {self.server_url}")
            if get_session_id:
                session_id = get_session_id()
                if session_id:
                    print(f"Session ID: {session_id}")

            try:
                response = await self.session.list_tools()
                self.tools = response.tools
                print("\nConnected to server with tools:", [tool.name for tool in self.tools])
                
                # Add tools information to the system message
                tools_info = "\n".join([f"- {tool.name}: {tool.description}" for tool in self.tools])
                self.messages[0] = SystemMessage(content=f"{self.messages[0].content}\n\nAvailable tools:\n{tools_info}")
            
            except Exception as e:
                logger.error(f"Error listing tools: {str(e)}", exc_info=True)
                raise

            # Run interactive loop
            await self.interactive_loop(session_id)
    async def cleanup(self):
        """Clean up resources"""
        logger.debug("Cleaning up resources")
        await self.exit_stack.aclose()

    async def interactive_loop(self,session_id:str):
        """Run interactive command loop."""
        print("\n🎯 Interactive MCP Client")
        print("Commands:")
        print("  list - List available tools")
        print("  call <tool_name> [args] - Call a tool")
        print("  quit - Exit the client")
        print()

        # Add the initial task to the conversation
        self.messages.append(HumanMessage(content=f"Task: {self.task}\n\nWhat should be my first step?"))

        task_complete = False
            
        while not task_complete:
            try:
                # Get Ollama's next recommendation
                print("\nSending current state to Ollama for analysis...")
                response = await self.llm.ainvoke(self.messages)
                print(f"\nOllama's analysis:\n{response.content}")
                
                # Add Ollama's response to the conversation history
                self.messages.append(AIMessage(content=response.content))
                
                # Parse the recommended action
                action = self._parse_next_action(str(response.content), session_id)
                if not action:
                    # Ask for a more specific action
                    self.messages.append(HumanMessage(content="Please provide a specific action to take using one of the available tools. Format your response as a JSON object with 'tool' and 'parameters' fields."))
                    continue
                
                # Check if the task is complete
                if action.get("tool") == "task_complete":
                    print("\nTask completed successfully!")
                    task_complete = True
                    break
                
                # Execute the recommended action
                tool_name = action["tool"]
                parameters = action["parameters"]
                
                # Handle session ID for browser actions
                if tool_name == "launch_browser" and self.session:
                    print(f"\nExecuting: {tool_name}")
                    print(f"Parameters: {json.dumps(parameters, indent=2)}")
                    
                    result = await self.session.call_tool(tool_name, parameters)
                    result_text = result.content[0].text # type: ignore
                    print(f"Result: {result_text}")
                    
                    # Store the session ID
                    session_id = result_text
                    
                elif session_id and self.session:
                    # Update the session ID in the parameters
                    parameters["session_id"] = session_id
                    
                    print(f"\nExecuting: {tool_name}")
                    print(f"Parameters: {json.dumps(parameters, indent=2)}")
                    
                    result = await self.session.call_tool(tool_name, parameters)
                    result_text = result.content[0].text # type: ignore
                    print(f"Result: {result_text}")
                    
                    # Special handling for screenshot results
                    if tool_name == "take_screenshot":
                        result_text = f"Screenshot saved. The browser window shows the current state of the page."
                elif self.session:
                    print(f"\nExecuting: {tool_name}")
                    print(f"Parameters: {json.dumps(parameters, indent=2)}")
                    
                    result = await self.session.call_tool(tool_name, parameters)
                    result_text = result.content[0].text # type: ignore
                    print(f"Result: {result_text}")
                
                # Add the result to the conversation
                self.messages.append(HumanMessage(content=f"Action result: {result_text}\n\nWhat should be my next step?"))
            except KeyboardInterrupt:
                logger.info("\nTask execution interrupted by user.")
                print("\n\n👋 Goodbye!")
                break
            except EOFError:
                break
            except Exception as e:
                logger.error(f"Error during execution: {str(e)}", exc_info=True)
                break
            finally:
                await self.cleanup()

    def _parse_next_action(self, response_text: str, session_id:str | None) -> Dict[str, Any] | None:
        """Parse the next action from Ollama's response
        
        Args:
            response_text: Ollama's response text
            
        Returns:
            Dictionary with tool name and parameters, or None if no valid action found
        """
        try:
            # Look for JSON blocks in the response
            json_pattern = r'```json\\s*([\\s\\S]*?)\\s*```'
            import re
            json_matches = re.findall(json_pattern, response_text)
            
            if json_matches:
                for json_str in json_matches:
                    try:
                        action = json.loads(json_str)
                        if isinstance(action, dict) and "tool" in action and "parameters" in action:
                            return action
                    except json.JSONDecodeError:
                        continue
            
            # If no JSON blocks, look for tool mentions in the text (only if tools are loaded)
            if hasattr(self, 'tools'):
                tool_names = [tool.name for tool in self.tools]
                for tool_name in tool_names:
                    if tool_name in response_text:
                        # Try to extract parameters from the text
                        params_start = response_text.find(tool_name) + len(tool_name)
                        params_text = response_text[params_start:].strip()
                        
                        # Simple heuristic to extract parameters
                        parameters = {}
                        if "url" in params_text.lower() and tool_name == "launch_browser":
                            url_match = re.search(r'https?://[^\s"\']+', params_text)
                            if url_match:
                                parameters["url"] = url_match.group(0)
                                return {"tool": tool_name, "parameters": parameters}
                        elif tool_name == "get_dom_structure":
                            parameters["max_depth"] = 3
                            parameters["session_id"] = session_id
                            return {"tool": tool_name, "parameters": parameters}
                        elif tool_name == "extract_data":
                            pattern_match = re.search(r'(?:)\[[\S\s]*\]', params_text)
                            if pattern_match:
                                parameters["pattern"] = pattern_match.group(0)
                                return {"tool": tool_name, "parameters": parameters}
                        elif tool_name == "click_selector" and  "selector" in params_text.lower():
                            pattern_match = re.search(r'(?<="selector": )\".+\"', params_text)                          
                            if pattern_match:
                                parameters["selector"] = pattern_match.group(0).strip('"')
                                return {"tool": tool_name, "parameters": parameters}  
                        elif tool_name == "click_element":
                            if "x" in params_text.lower() and "y" in params_text.lower():
                                pattern_match = re.search(r'x":\s*([^,]*),.*\s*?"y":\s*([^,]*)', params_text)                          
                                if pattern_match:
                                    parameters["x"] = pattern_match.group(1)
                                    parameters["y"] = pattern_match.group(2)
                                    return {"tool": tool_name, "parameters": parameters}
                            elif "coordinates" in params_text.lower():
                                pattern_match = re.findall(r'\d+', params_text)                                  
                                if pattern_match:
                                    parameters["x"] = pattern_match[0]
                                    parameters["y"] = pattern_match[1]
                                    return {"tool": tool_name, "parameters": parameters}
                        elif tool_name == "scroll_page" and "direction" in params_text.lower():
                            pattern_match = re.search(r'(?<="direction": )\".+\"', params_text)                          
                            if pattern_match:
                                parameters["direction"] = pattern_match.group(0).strip('"')
                                return {"tool": tool_name, "parameters": parameters}

                        elif tool_name == "take_screenshot" \
                            or tool_name == "get_page_content" :
                            parameters["session_id"] = session_id
                            return {"tool": tool_name, "parameters": parameters}

            
            # If task completion is mentioned
            if "task complete" in response_text.lower() or "task is complete" in response_text.lower():
                return {"tool": "task_complete", "parameters": {}}
                
            return None
            
        except Exception as e:
            logger.warning(f"Failed to parse next action: {e}")
            return None


async def main():   
    server_url = 5600
    transport_type = "streamable-http"
    server_url = f"http://localhost:{server_url}/mcp"

    print("MCP Client using Ollama")
    print(f"Connecting to: {server_url}")
    print(f"Transport type: {transport_type}")

    parser = argparse.ArgumentParser(description="Interactive browser automation with Ollama")
    parser.add_argument("task", nargs='?', help="Task description")
    args = parser.parse_args()
    print(f"executing Task: {args.task}")
    if not args.task:
         args.task = "Navigate to Ollama's model library, analyze the page content, and extract information about the available models."

    # Start connection flow - OAuth will be handled automatically
    client = MCPClient(server_url, transport_type, args.task)
    await client.connect()

if __name__ == "__main__":
    asyncio.run(main())