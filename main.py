import asyncio
import argparse
from llama_index.tools.mcp import BasicMCPClient
from llama_index.tools.mcp import (
    get_tools_from_mcp_url,
    aget_tools_from_mcp_url,
)
from llama_index.core.agent import FunctionAgent
from llama_index.core.agent.workflow import AgentStream
from llama_index.core import Settings
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama
from rag import add_rag_args, setup_rag_tools

OKGREEN = "\033[92m"
BOLD = "\033[1m"
ENDC = "\033[0m"

CONTEXT_WINDOW = 8000


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
        "-e",
        "--embed-model",
        type=str,
        default="bge-m3",
        help="The name of the embedding model to use.",
    )
    add_rag_args(parser)
    args = parser.parse_args()
    base_url = f"http://{args.host}:11434"
    llm = Ollama(
        model=args.model,
        base_url=base_url,
        context_window=CONTEXT_WINDOW,
        request_timeout=120.0,
    )
    Settings.llm = llm
    Settings.embed_model = OllamaEmbedding(
        model_name=args.embed_model,
        base_url=base_url,
    )

    local_client = BasicMCPClient("http://localhost:8080/sse")
    tools = await aget_tools_from_mcp_url(
        "http://localhost:8080/sse", client=local_client
    )
    tools.extend(setup_rag_tools(args))

    agent = FunctionAgent(
        tools=tools,
        llm=llm,
        system_prompt=(
            "You are a system expert specializing in the Network Exposure "
            "Function (NEF) of 5G networks. Your role is to accurately "
            "understand the user’s request and generate precise curl commands "
            "that perform the required NEF operations. To accomplish this, you "
            "must fully comprehend the user’s intent, consult the NEF API "
            "documentation or relevant 3GPP references, read the traffic "
            "influence open api description and use all available tools and "
            "knowledge to ensure correctness."
        ),
    )

    print(f"Agent initialized with Ollama model: {args.model}.")
    print("Type 'exit' to quit.")
    while True:
        query = input(f"{BOLD}You: {ENDC} ")
        if query.lower() == "exit":
            break
        handler = agent.run(user_msg=query)
        print(f"{OKGREEN}", end="")
        async for event in handler.stream_events():
            if isinstance(event, AgentStream):
                print(event.delta, end="", flush=True)
        print(f"{ENDC}")


if __name__ == "__main__":
    asyncio.run(main())
