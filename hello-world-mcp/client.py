"""
MCP CLIENT: The AI Reasoning Engine
-----------------------------------
ROLE: This is the 'Brain'. It manages the conversation history, calls the 
Gemini API, and handles the low-level communication pipes to the server.
"""

import asyncio
import sys
import logging
from dotenv import load_dotenv
from google import genai
from google.genai import types
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# 1. THE WINDOWS PROACTOR FIX:
# By default, Windows uses a "Selector" event loop which can't handle 
# subprocess pipes. We force it to use "Proactor" to prevent the 'Hang'.
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# 2. LOGGING & ENV:
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')
load_dotenv(override=True)
client = genai.Client() # Grabs GEMINI_API_KEY from .env automatically

async def run_chat_interface():
    """
    Main Asynchronous Loop. This function 'awaits' responses so the
    program stays responsive while waiting for the AI or Database.
    """
    
    # "-u" forces 'Unbuffered' mode. This prevents Windows from 'holding' 
    # data in a secret buffer, ensuring the Client sees the Server's output instantly.
    server_params = StdioServerParameters(command="python", args=["-u", "server.py"])
    
    try:
        # 'async with' ensures that if the code crashes, the pipes are closed cleanly.
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Handshake: Client says hello to Server
                await session.initialize()
                print("\n✅ MCP System Ready. (Persistent DB: school.db)")
                
                # DISCOVERY: Ask the server what tools it has
                server_tools = await session.list_tools()
                
                # SCHEMA TRANSLATION:
                # Gemini expects OpenAPI (UPPERCASE) types. MCP provides JSON (lowercase).
                # We loop through and 'fix' the labels so Gemini understands them.
                gemini_tools = []
                for t in server_tools.tools:
                    props = {}
                    for k, v in t.inputSchema.get("properties", {}).items():
                        props[k] = {"type": str(v.get("type", "string")).upper()}
                    
                    gemini_tools.append({
                        "name": t.name,
                        "description": t.description,
                        "parameters": {
                            "type": "OBJECT",
                            "properties": props,
                            "required": t.inputSchema.get("required", [])
                        }
                    })
                    print(f"🔧 Tool Synced: {t.name}")

                # THE CONVERSATION MEMORY:
                # This list grows with every message, giving the AI 'History'.
                messages = []
                
                while True:
                    try:
                        user_input = input("\n👤 You: ")
                    except EOFError: break
                    if user_input.lower() in ['exit', 'quit']: break
                    
                    # Store user's question
                    messages.append(types.Content(role="user", parts=[types.Part.from_text(text=user_input)]))
                    
                    # THE RE-ACT LOOP:
                    # The AI might need to call multiple tools to answer one question.
                    while True:
                        logging.info("Gemini is thinking...")
                        response = client.models.generate_content(
                            model="gemini-2.5-flash",
                            contents=messages,
                            config=types.GenerateContentConfig(
                                tools=[{"function_declarations": gemini_tools}],
                                system_instruction="You are a school admin. Use tools to get data."
                            )
                        )
                        
                        # Add AI's response/thought to history
                        messages.append(response.candidates[0].content)
                        
                        # Check if AI wants to use a Tool
                        if response.function_calls:
                            for call in response.function_calls:
                                logging.info(f"AI Calling Server Tool: {call.name}")
                                
                                # Call the background server and 'await' the data
                                tool_result = await session.call_tool(call.name, arguments=dict(call.args))
                                result_text = tool_result.content[0].text
                                
                                # Feed the database result back to the AI
                                messages.append(types.Content(role="user", parts=[
                                    types.Part.from_function_response(name=call.name, response={"result": result_text})
                                ]))
                        else:
                            # If no more tools are needed, show the final answer
                            print(f"\n🤖 Agent: {response.text}")
                            break

    except Exception as e:
        logging.error(f"Fatal System Error: {e}")
    finally:
        logging.info("Shutting down. All background processes killed.")

if __name__ == "__main__":
    try:
        # Start the asynchronous 'Event Loop'
        asyncio.run(run_chat_interface())
    except KeyboardInterrupt:
        sys.exit(0)