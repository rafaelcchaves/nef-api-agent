import asyncio
import argparse
import time
import json
import tiktoken
from typing import Any, Dict, List, Optional
from llama_index.core.callbacks import CallbackManager, TokenCountingHandler, CBEventType, EventPayload
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
from rag.rag import RAGPipeline
import sys


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
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging of LLM prompts and inputs."
    )
    parser.add_argument(
        "query", type=str, help="The query to be processed by the agent."
    )
    args = parser.parse_args()        
    # Setup Token Counting
    token_counter = TokenCountingHandler(
        tokenizer=tiktoken.get_encoding("cl100k_base").encode
    )
    
    handlers = [token_counter]
    Settings.callback_manager = CallbackManager(handlers)

    base_url = f"http://{args.host}:11434"
    llm = Ollama(
        streaming = True,
        thinking = True,
        model=args.model,
        base_url=base_url,
        keep_alive = "2m",
        context_window=CONTEXT_WINDOW,
        request_timeout=120.0,
    )
    Settings.llm = llm

    local_client = BasicMCPClient(args.mcp_server)
    tools = await aget_tools_from_mcp_url(
        args.mcp_server, client=local_client
    )

    rag = RAGPipeline(host=args.host, llm_model=args.model)
    tools.extend(rag.get_tools()) # Changed from .append(rag.get_tool()) to .extend(rag.get_tools())

    if args.verbose:
        tool_names = [t.metadata.name for t in tools]
        print(f"--- Loaded Tools: {tool_names} ---")

    prompt = (
        "You are a helpful agent.\n"
        "You are a system expert specialized in the Network Exposure Function (NEF) of 5G networks.\n"
        "Your role is to accurately understand the user’s request and use the available tools to perform the required operations.\n"
        "\n"
        "STRICT EXECUTION PLAN:\n"
        "1. First, you MUST call the tool 'get_subscription_schema' to retrieve the valid JSON structure for 'subscription_data'. DO NOT guess the structure.\n"
        "2. Analyze the user's request and map it to the schema fields you just retrieved.\n"
        "3. Verbalize your plan using 'Thought: ...' to explain how you constructed the payload.\n"
        "4. Finally, call 'add_subscription' with the correctly formatted 'subscription_data'.\n"
        "\n"
        "CRITICAL: You are FORBIDDEN from calling 'add_subscription' without first calling 'get_subscription_schema'.\n"
    )
    
    if args.verbose:
        print("\n--- System Prompt ---\n")
        print(prompt)
        print("\n---------------------\n")

    agent = FunctionAgent(
        tools=tools,
        llm=llm,
        system_prompt=prompt
    )
    chat_history = []

    query = args.query

    if args.verbose:
        print("\n--- User Query ---\n")
        print(query)
        print("\n------------------\n")

    token_counter.reset_counts() 
    start_time = time.time()

    handler = agent.run(user_msg=query, chat_history=chat_history)
    
    response = ""
    async for event in handler.stream_events():
        if isinstance(event, AgentStream):
            response += event.delta
        elif args.verbose and hasattr(event, 'tool_name') and hasattr(event, 'tool_kwargs'): # For ToolCall
            print(f"\n--- Tool Call: {event.tool_name} ---\n")
            print(f"Arguments: {json.dumps(event.tool_kwargs, indent=2)}")
            print("\n-----------------------\n")
        elif args.verbose and hasattr(event, 'tool_output'): # For ToolOutput
            print(f"\n--- Tool Output ---\n")
            print(str(event.tool_output))
            print("\n-------------------\n")
    
    if response:
        print("\n--- Agent Response ---\n")
        print(response)
        print("\n----------------------\n")
    else:
        print("\n--- Error ---\n")
        print("No response generated. The model might have failed to produce output or encountered an error.")
        print("\n-------------\n")

    end_time = time.time()
    processing_time = end_time - start_time

    metrics_content = (
        f"Processing Time:       {processing_time:.4f} seconds\n"
        f"Embedding Tokens:      {token_counter.total_embedding_token_count}\n"
        f"LLM Prompt Tokens:     {token_counter.prompt_llm_token_count}\n"
        f"LLM Completion Tokens: {token_counter.completion_llm_token_count}\n"
        f"Total LLM Token Count: {token_counter.total_llm_token_count}"
    )
    print("\n--- METRICS ---\n")
    print(metrics_content)
    print("\n---------------\n")
    
    chat_history.append(ChatMessage(role="assistant", content=response))

if __name__ == "__main__":
    asyncio.run(main())
