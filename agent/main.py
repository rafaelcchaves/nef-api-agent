import asyncio
import argparse
import time
import json
import ast
import re
import tiktoken
from typing import Any, Dict, List, Optional
from llama_index.core.callbacks import CallbackManager, TokenCountingHandler, CBEventType, EventPayload
from llama_index.tools.mcp import BasicMCPClient
from llama_index.core.agent.workflow.workflow_events import ToolCallResult, ToolCall, AgentOutput
from llama_index.tools.mcp import (
    get_tools_from_mcp_url,
    aget_tools_from_mcp_url,
)
from llama_index.core.agent import FunctionAgent
from llama_index.core.agent.workflow import AgentStream
from llama_index.core.llms import ChatMessage
from llama_index.core import Settings
from mcp.types import CallToolResult
from llama_index.llms.ollama import Ollama
from rag.rag import RAGPipeline
from llama_index.core.callbacks.base_handler import BaseCallbackHandler
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
        "-t", "--thinking", action="store_true", help="Enable thinking mode."
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
        thinking = args.thinking,
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

    prompt = (
        "You are a helpful agent.\n"
        "You are a system expert specialized in the Network Exposure Function (NEF) of 5G networks.\n"
        "Your role is to accurately understand the user’s request and use the available tools to perform the required operations.\n"
        "\n"
        "STRICT EXECUTION PLAN:\n"
        "1. First, you MUST call the tool 'get_subscription_schema' to retrieve the valid JSON structure for 'subscription_data'. DO NOT guess the structure.\n"
        "2. Analyze the user's request and map it to the schema fields you just retrieved.\n"
        "3. Verbalize your plan to explain how you constructed the payload.\n"
        "4. Finally, call 'add_subscription' with the correctly formatted 'subscription_data'.\n"
        "\n"
        "CRITICAL: You are FORBIDDEN from calling 'add_subscription' without first calling 'get_subscription_schema'.\n"
    )

    agent = FunctionAgent(
        tools=tools,
        llm=llm,
        system_prompt=prompt
    )
    chat_history = []

    query = args.query

    # Print initial system prompt and user query once
    print(f"\n[SYSTEM PROMPT]\n\n{prompt}")
    print(f"\n[USER PROMPT]\n\n{query}")

    token_counter.reset_counts() 
    start_time = time.time()

    handler = agent.run(user_msg=query, chat_history=chat_history)
    state = "init"
    response = ""
    print("\n[RESPONSE]\n") 
    async for event in handler.stream_events():
        if isinstance(event, AgentStream):
            if event.thinking_delta:
                if state != "thinking":
                    print("\n<think/>")
                    state = "thinking"
                print(event.thinking_delta, end="", flush=True)
            elif event.delta:
                if state == "thinking":
                    print("</think>")
                response += event.delta
                print(event.delta, end="", flush=True)
                state = "response"
        else:
            if state == "thinking": 
                print("</think>")
            if isinstance(event, ToolCall): # For ToolOutput
                print("\n[TOOL CALL]\n")
                print(event.tool_name)
                print(json.dumps(event.tool_kwargs, indent=4))
                state = "tool_call"
            elif isinstance(event, ToolCallResult):
                print("\n[TOOL RESPONSE]\n")
                print(event.tool_name)
                output = event.tool_output.raw_output
                if isinstance(output, CallToolResult):
                    print(json.dumps(output.structuredContent, indent=4))
                elif isinstance(output, dict):
                    print(json.dumps(output, indent=4))
                print()
                state = "tool_response"
            elif isinstance(event, AgentOutput):
                state = "output"
            else:
                state = "unknown"


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
