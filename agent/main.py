import asyncio
import argparse
from llama_index.tools.mcp import BasicMCPClient
from llama_index.tools.mcp import (
    get_tools_from_mcp_url,
    aget_tools_from_mcp_url,
)
from llama_index.core.agent import FunctionAgent
from llama_index.core.agent.workflow import AgentStream
from llama_index.core.llms import ChatMessage
from llama_index.core import Settings

from llama_index.llms.ollama import Ollama
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax



CONTEXT_WINDOW = 16000


async def main():
    parser = argparse.ArgumentParser(description="Run a LlamaIndex function agent.")
    parser.add_argument(
        "-m",
        "--model",
        type=str,
        default="llama3.2:latest",
        help="The name of the Ollama model to use (e.g., 'llama2', 'mistral').",
    )
    parser.add_argument(
        "-H",
        "--host",
        type=str,
        default="localhost",
        help="The host for the Ollama models.",
    )


    parser.add_argument(
        "-M",
        "--mcp-server",
        type=str,
        default="http://localhost:8080/sse",
        help="The URL of the MCP server.",
    )


    args = parser.parse_args()
    base_url = f"http://{args.host}:11434"
    llm = Ollama(
        model=args.model,
        base_url=base_url,
        keep_alive = "2m",
        thinking = True,
        context_window=CONTEXT_WINDOW,
        request_timeout=120.0,
    )
    Settings.llm = llm

    local_client = BasicMCPClient(args.mcp_server)
    tools = await aget_tools_from_mcp_url(
        args.mcp_server, client=local_client
    )

    prompt = ''' 
        You are a helpful agent.
        You are a system expert specialized in the Network Exposure Function (NEF) of 5G networks.
        Your role is to accurately understand the user’s request and use the available tools to perform the required operations.
    '''

    agent = FunctionAgent(
        tools=tools,
        llm=llm,
        system_prompt=prompt
    )

    console = Console()
    chat_history = []
    console.print(f"Agent initialized with Ollama model: [bold]{args.model}[/bold].")
    console.print("Type 'exit' to quit.")
    while True:
        query = console.input(f"[bold]You: [/bold]")
        if query.lower() == "exit":
            break
        
        chat_history.append(ChatMessage(role="user", content=query))
        handler = agent.run(user_msg=query, chat_history=chat_history)
        
        response = ""
        console.print(f"[green]Agent:", end="")
        async for event in handler.stream_events():
            if isinstance(event, AgentStream):
                response += event.delta
                console.print(event.delta, end="", style="green")
        console.print()
        break

        
        chat_history.append(ChatMessage(role="assistant", content=response))

if __name__ == "__main__":
    asyncio.run(main())
