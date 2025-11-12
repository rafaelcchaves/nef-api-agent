import argparse
import chromadb
from llama_index.core import Settings, VectorStoreIndex
from llama_index.core.tools import FunctionTool
from llama_index.vector_stores.chroma import ChromaVectorStore

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
    """Search NEF documentation for concepts in the user's question."""
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
    description="Consult the traffic influence OPEN-API description.",
)

run_rag_tool = FunctionTool.from_defaults(
    fn=lambda question: consult_nef_documentation(
        question=question,
    ),
    name="consult_nef_documentation",
    description="Search NEF documentation for concepts in the user's question.",
)

def add_rag_args(parser: argparse.ArgumentParser):
    parser.add_argument(
        "-c",
        "--collection",
        type=str,
        default="RAG_ARTICLE",
        help="The name of the ChromaDB collection.",
    )
    parser.add_argument(
        "-k",
        "--top-k",
        type=int,
        default=5,
        help="The number of similar documents to retrieve.",
    )
    parser.add_argument(
        "-db",
        "--db-dir",
        type=str,
        default="./chroma_db",
        help="The directory of the ChromaDB database.",
    )
    parser.add_argument(
        "--rag", action="store_true", help="Enable the RAG pipeline tool."
    )

def setup_rag_tools(args: argparse.Namespace) -> list[FunctionTool]:
    tools = []
    if args.rag:
        Settings.rag_collection = args.collection
        Settings.rag_top_k = args.top_k
        Settings.rag_db_dir = args.db_dir
        tools.append(consult_traffic_influence_api_tool)
        tools.append(run_rag_tool)
    return tools