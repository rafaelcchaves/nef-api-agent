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

OKGREEN = '\033[92m'
BOLD = '\033[1m'
ENDC = '\033[0m'

CONTEXT_WINDOW=8000

def consult_traffic_influence_api() -> str:
    """Consult the traffic influence OPEN-API description."""
    print("\nDOCUMETATION\n")
    file_path = "./documents/ti_api.txt"
    with open(file_path, "r") as f:
        content = f.read()
    return content

def consult_nef_documentation(
    question: str,
) -> str:
    """Search in Network Exposure Function Documentation text and concepts related to the question string parameter."""
    print("\nRAG\n")
    db = chromadb.PersistentClient(path=Settings.rag_db_dir)
    chroma_collection = db.get_collection(Settings.rag_collection)
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    index = VectorStoreIndex.from_vector_store(vector_store=vector_store)

    query_engine = index.as_query_engine(similarity_top_k=Settings.rag_top_k)
    response = query_engine.query(question)

    return str(response)

consult_traffic_influence_api_tool = FunctionTool.from_defaults(
    fn=consult_traffic_influence_api,
    name="consult_traffic_influence_api",
    description="Consult the traffic influence OPEN-API description."
)

run_rag_tool = FunctionTool.from_defaults(
    fn=lambda question: consult_nef_documentation(
        question=question,
    ),
    name="consult_nef_documentation",
    description="Search in Network Exposure Function Documentation text and concepts related to the question string parameter."
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

    tools = []
    if args.rag:
        tools.append(consult_traffic_influence_api_tool)
        tools.append(run_rag_tool)

    agent = FunctionAgent(
        tools=tools,
        llm=llm,
        system_prompt="BE CONCISE, BE DIRECT IN YOUR ANSWERS, DO NOT DETAIL. You are a system expert specializing in the Network Exposure Function (NEF) of 5G networks. Your role is to accurately understand the user’s request and generate precise curl commands that perform the required NEF operations. To accomplish this, you must fully comprehend the user’s intent, consult the NEF API documentation or relevant 3GPP references, read the traffic influence open api description and use all available tools and knowledge to ensure correctness. Every curl command you produce should be syntactically accurate, secure, and include appropriate headers, authentication tokens, parameters, and HTTP methods according to the API specification. Your responses must be clear, ready-to-execute examples that reflect best practices in 5G NEF data exposure and security. Accuracy, completeness, and understanding of the user’s intent are vital before generating the final output."
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
