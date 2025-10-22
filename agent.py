import asyncio
import os
import argparse
from llama_index.core.agent import FunctionAgent
from llama_index.core.agent.workflow import AgentStream
from llama_index.core import Settings, VectorStoreIndex
from llama_index.core.tools import FunctionTool
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb

CONTEXT_WINDOW=8000

def get_traffic_influence_api_definition() -> str:
    """Useful for getting the documentation of the traffic influence API."""
    file_path = "./documents/ti_api.txt"
    with open(file_path, "r") as f:
        content = f.read()
    return content

def run_rag_pipeline(
    question: str,
) -> str:
    """Useful for answering questions using a RAG pipeline.
    The question to ask the RAG pipeline is 'question'.
    """
    db = chromadb.PersistentClient(path=Settings.rag_db_dir)
    chroma_collection = db.get_collection(Settings.rag_collection)
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    index = VectorStoreIndex.from_vector_store(vector_store=vector_store)

    query_engine = index.as_query_engine(similarity_top_k=Settings.rag_top_k)
    response = query_engine.query(question)

    return str(response)

get_traffic_influence_api_definition_tool = FunctionTool.from_defaults(fn=get_traffic_influence_api_definition)

run_rag_tool = FunctionTool.from_defaults(
    fn=lambda question: run_rag_pipeline(
        question=question,
    ),
    name="run_rag_pipeline",
    description="Useful for answering questions using a RAG pipeline."
)



async def main():
    parser = argparse.ArgumentParser(description="Run a LlamaIndex function agent.")
    parser.add_argument("-m", "--model", type=str, default="llama3.2:latest", help="The name of the Ollama model to use (e.g., 'llama2', 'mistral').")
    parser.add_argument("-H", "--host", type=str, default="localhost", help="The host for the Ollama models.")
    parser.add_argument("-c", "--collection", type=str, default="RAG_ARTICLE", help="The name of the ChromaDB collection.")
    parser.add_argument("-k", "--top-k", type=int, default=5, help="The number of similar documents to retrieve.")
    parser.add_argument("-e", "--embed-model", type=str, default="bge-m3", help="The name of the embedding model to use.")
    parser.add_argument("-db", "--db-dir", type=str, default="./chroma_db", help="The directory of the ChromaDB database.")
    parser.add_argument("--rag", action="store_true", help="Enable the RAG pipeline tool.")
    args = parser.parse_args()
    print(args.model)
    base_url = f"http://{args.host}:11434"
    llm = Ollama(model=args.model, base_url=base_url, context_window=CONTEXT_WINDOW, request_timeout=120.0)
    Settings.llm = llm
    Settings.embed_model = OllamaEmbedding(
        model_name=args.embed_model,
        base_url=base_url,
    )
    Settings.rag_collection = args.collection
    Settings.rag_top_k = args.top_k
    Settings.rag_db_dir = args.db_dir

    tools = [get_traffic_influence_api_definition_tool]
    if args.rag:
        tools.append(run_rag_tool)

    agent = FunctionAgent(
        verbose=True,
        tools=tools,
        llm=llm,
        system_prompt="You are a system expert specializing in the Network Exposure Function (NEF) of 5G networks. Your role is to accurately understand the user’s request and generate precise curl commands that perform the required NEF operations. To accomplish this, you must fully comprehend the user’s intent, consult the NEF API documentation or relevant 3GPP references, and use all available tools and knowledge to ensure correctness. Every curl command you produce should be syntactically accurate, secure, and include appropriate headers, authentication tokens, parameters, and HTTP methods according to the API specification. Your responses must be clear, ready-to-execute examples that reflect best practices in 5G NEF data exposure and security. Accuracy, completeness, and understanding of the user’s intent are vital before generating the final output."
    )

    print(f"Agent initialized with Ollama model: {args.model}.")
    print("Type 'exit' to quit.")
    while True:
        query = input("You: ")
        if query.lower() == "exit":
            break
        handler = agent.run(user_msg=query)
        async for event in handler.stream_events():
            if isinstance(event, AgentStream):
                print(event.delta, end="", flush=True)
        print()

if __name__ == "__main__":
    asyncio.run(main())
