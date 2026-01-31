import asyncio
import argparse
import time
import json
import tiktoken
import os
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from llama_index.core.callbacks import CallbackManager, TokenCountingHandler
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
from llama_index.llms.anthropic import Anthropic
from llama_index.core.callbacks.base_handler import BaseCallbackHandler
import sys

# Load environment variables from .env file
load_dotenv()





CONTEXT_WINDOW = 16000

# 3GPP Traffic Influence Subscription Schema
SUBSCRIPTION_SCHEMA = {
    "type": "object",
    "properties": {
        "afServiceId": {"type": "string", "description": "Identifier of the AF service"},
        "dnn": {"type": "string", "description": "Data Network Name"},
        "snssai": {
            "type": "object",
            "properties": {
                "sst": {"type": "integer", "description": "Slice/Service Type"},
                "sd": {"type": "string", "description": "Slice Differentiator"}
            },
            "required": ["sst", "sd"]
        },
        "anyUeInd": {"type": "boolean", "description": "Indicates whether the subscription applies to any UE"},
        "notificationDestination": {"type": "string", "description": "URL to send notifications"},
        "trafficFilters": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "flowId": {"type": "integer", "description": "Flow identifier"},
                    "flowDescriptions": {
                        "type": "array",
                        "items": {"type": "string", "description": "Description of the traffic flow (e.g., IP filter)"}
                    }
                },
                "required": ["flowId", "flowDescriptions"]
            }
        },
        "trafficRoutes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "dnai": {"type": "string", "description": "Data Network Access Identifier"}
                },
                "required": ["dnai"]
            }
        },
        "appReloInd": {"type": "boolean", "description": "Indicates whether application relocation is allowed (for PATCH/PUT)"}
    },
    "required": [
        "afServiceId",
        "dnn",
        "snssai",
        "anyUeInd",
        "notificationDestination",
        "trafficFilters",
        "trafficRoutes"
    ]
}

async def main():
    parser = argparse.ArgumentParser(description="Run a LlamaIndex function agent.")
    parser.add_argument(
        "-m",
        "--model",
        type=str,
        default="llama3.2:latest",
        help="The model to use. Use 'claude-...' for Anthropic Claude models (requires ANTHROPIC_API_KEY), or Ollama model names (e.g., 'llama3.2:latest', 'mistral') for local models.",
    )
    parser.add_argument(
        "-H",
        "--host",
        type=str,
        default="localhost",
        help="The host for the Ollama models (ignored for Gemini models).",
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
        "--context_insertion", action="store_true", help="Include the schema directly in the system prompt."
    )
    parser.add_argument(
        "-s", "--streaming", action="store_true", help="Enable streaming response mode."
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

    # Choose LLM provider based on model name
    if args.model.lower().startswith("claude"):
        # Use Anthropic API for Claude models
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            print("\n[FATAL ERROR] ANTHROPIC_API_KEY not found in environment variables.")
            print("Please add ANTHROPIC_API_KEY to your .env file.")
            sys.exit(1)
        
        llm = Anthropic(
            model=args.model,
            api_key=api_key,
            max_tokens=12000,  # Must be greater than thinking budget
            thinking_dict={"type": "enabled", "budget_tokens": 8000},
        )
    else:
        # Use Ollama for local models
        base_url = f"http://{args.host}:11434"
        llm = Ollama(
            streaming=args.streaming,
            model=args.model,
            base_url=base_url,
            keep_alive="2m",
            context_window=CONTEXT_WINDOW,
            request_timeout=120.0,
        )
    Settings.llm = llm

    local_client = BasicMCPClient(args.mcp_server)
    try:
        tools = await aget_tools_from_mcp_url(
            args.mcp_server, client=local_client
        )
    except Exception as e:
        print(f"\n[FATAL ERROR] Could not connect to MCP server at {args.mcp_server}.")
        print("Please confirm if the MCP server is running and accessible at the specified host/URL.")
        sys.exit(1)

    query = args.query

    # Build system prompt based on whether --context_insertion flag is used
    if args.context_insertion:
        prompt = f"""You are an autonomous 5G Network Exposure Function (NEF) agent that receives natural language requests and use the available tools to execute traffic influence API and calls without user interaction. Execute operations independently while maintaining precision and transparency.

**Schema Reference:**
{json.dumps(SUBSCRIPTION_SCHEMA, indent=2)}

**Autonomous Execution Protocol:**

1. **Analyze**: Parse the user prompt to extract all possible parameters
2. **Map & Infer**: Explicitly document how you map natural language elements to schema fields. For any missing required fields:
   - Make reasonable, documented inferences from context
   - Apply sensible defaults when no context exists (e.g., 24h time window, current timestamp)
   - If critical fields are unresolvable, proceed with best-effort and flag the ambiguity
3. **Plan**: Output a structured execution plan showing:
   - Mapped parameters with values
   - Assumptions made
   - Default values used
   - Tool(s) to be invoked
4. **Execute**: Perform the API operation immediately using available tools
5. **Complete**: When the task is completed, clearly inform the user that the operation has been successfully executed and end the call

**Critical Constraints:**
- Never fail silently—always document inference logic
- Prefer conservative defaults over risky assumptions
- If multiple interpretations exist, select the most probable and note alternatives
- Log all parameter mappings for auditability
- Treat ambiguities as warnings, not blockers
- When task is completed, immediately inform completion and end"""
    else:
        prompt = """You are an autonomous 5G Network Exposure Function (NEF) agent that receives natural language requests and use the available tools to execute traffic influence API calls without user interaction. Execute operations independently while maintaining precision and transparency.

**Autonomous Execution Protocol:**

1. **Analyze**: Parse the user prompt to extract all possible parameters
2. **Map & Infer**: Explicitly document how you map natural language elements to schema fields. For any missing required fields:
   - Make reasonable, documented inferences from context  
   - Apply sensible defaults when no context exists (e.g., 24h time window, current timestamp)
   - If critical fields are unresolvable, proceed with best-effort and flag the ambiguity
3. **Plan**: Output a structured execution plan showing:
   - Mapped parameters with values
   - Assumptions made
   - Default values used
   - Tool(s) to be invoked
4. **Execute**: Perform the API operation immediately using available tools
5. **Complete**: When the task is completed, clearly inform the user that the operation has been successfully executed and end the call

**Critical Constraints:**
- Never fail silently—always document inference logic
- Prefer conservative defaults over risky assumptions
- If multiple interpretations exist, select the most probable and note alternatives
- Log all parameter mappings for auditability
- Treat ambiguities as warnings, not blockers
- When task is completed, immediately inform completion and end"""


    agent = FunctionAgent(
        tools=tools,
        llm=llm,
        system_prompt=prompt
    )
    chat_history = []

    # Print initial system prompt and user query once
    print(f"\n[SYSTEM PROMPT]\n\n{prompt}")
    print(f"\n[USER PROMPT]\n\n{query}")

    token_counter.reset_counts() 
    start_time = time.time()

    # Execute based on streaming mode
    print("\n[RESPONSE]\n")
    if args.streaming:
        # Streaming mode: process events as they arrive
        handler = agent.run(user_msg=query, chat_history=chat_history)
        state = "init"
        response = ""
        async for event in handler.stream_events():
            if isinstance(event, AgentStream):
                if event.thinking_delta:
                    if state != "thinking":
                        print("\n<think>")
                        state = "thinking"
                    print(event.thinking_delta, end="", flush=True)
                elif event.delta:
                    if state == "thinking":
                        print("\n</think>")
                    response += event.delta
                    print(event.delta, end="", flush=True)
                    state = "response"
            else:
                if state == "thinking":
                    print("\n</think>")
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
    else:
        # Non-streaming mode: get complete response
        response_obj = await agent.run(user_msg=query, chat_history=chat_history)
        response = response_obj.response
        print(response, end="", flush=True)


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
