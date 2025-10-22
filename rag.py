import argparse
from llama_index.core import Settings, VectorStoreIndex
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb

def main(question, llm_model, host, collection, top_k, embed_model, db_dir, rag_enabled):
    if rag_enabled:
        print("--- Starting RAG Pipeline ---")
    else:
        print("--- Starting LLM (RAG disabled) ---")

    base_url = f"http://{host}:11434"

    print(f"Initializing LLM: {llm_model}...")
    llm = Ollama(model=llm_model, base_url=base_url, context_window=20000, request_timeout=120.0)
    Settings.llm = llm
    print("LLM initialized.")

    if rag_enabled:
        print(f"Initializing embedding model: {embed_model}...")
        Settings.embed_model = OllamaEmbedding(
            model_name=embed_model,
            base_url=base_url,
        )
        print("Embedding model initialized.")

        print(f"Loading vector store from '{db_dir}' and collection '{collection}'...")
        db = chromadb.PersistentClient(path=db_dir)
        chroma_collection = db.get_collection(collection)
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
        print("Vector store loaded.")

        print("Creating query engine...")
        query_engine = index.as_query_engine(similarity_top_k=top_k)
        print("Query engine created.")

        print("\n--- Making Query ---")
        print(f"Question: {question}")
        response = query_engine.query(question)

        #print("\n--- Source Nodes ---")
        #for i, node in enumerate(response.source_nodes):
        #    print(f"\n[Node {i+1}]\n")
        #    print(node.get_content())
    else:
        print("\n--- Making Query ---")
        print(f"Question: {question}")
        response = llm.complete(question)

    print("\n\n--- Response ---")
    print(response)
    print("\n--------------------\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a RAG pipeline.")
    parser.add_argument("-q", "--question", type=str, required=True, help="The question to ask the RAG pipeline.")
    parser.add_argument("-m", "--llm-model", type=str, default="llama3.2:latest", help="The name of the language model to use.")
    parser.add_argument("-H", "--host", type=str, default="localhost", help="The host for the Ollama models.")
    parser.add_argument("-c", "--collection", type=str, default="RAG_ARTICLE", help="The name of the ChromaDB collection.")
    parser.add_argument("-k", "--top-k", type=int, default=5, help="The number of similar documents to retrieve.")
    parser.add_argument("-e", "--embed-model", type=str, default="bge-m3", help="The name of the embedding model to use.")
    parser.add_argument("-db", "--db-dir", type=str, default="./chroma_db", help="The directory of the ChromaDB database.")
    parser.add_argument("--rag", action="store_true", help="Enable RAG pipeline.")
    args = parser.parse_args()

    main(args.question, args.llm_model, args.host, args.collection, args.top_k, args.embed_model, args.db_dir, args.rag)
