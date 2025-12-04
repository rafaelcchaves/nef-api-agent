import argparse
import os
import logging
import sys

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.readers.file import PyMuPDFReader

# Configure logging
#logging.basicConfig(stream=sys.stdout, level=logging.INFO)
#logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

# Constants
DEFAULT_DOCS_DIR = "documents"
DEFAULT_VECTOR_STORE_DIR = "vector_store"

def main():
    parser = argparse.ArgumentParser(description="Create a LlamaIndex vector store from documents.")
    parser.add_argument(
        "-i",
        "--input-dir",
        type=str,
        default=DEFAULT_DOCS_DIR,
        help=f"Path to the directory containing documents (default: {DEFAULT_DOCS_DIR})",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=str,
        default=DEFAULT_VECTOR_STORE_DIR,
        help=f"Path to the directory to save the vector store (default: {DEFAULT_VECTOR_STORE_DIR})",
    )
    parser.add_argument(
        "-e",
        "--embed-model",
        type=str,
        default="qwen3-embedding:0.6b",
        help="The name of the Ollama embedding model to use (e.g., 'nomic-embed-text').",
    )
    parser.add_argument(
        "-H",
        "--host",
        type=str,
        default="localhost",
        help="The host for the Ollama instance.",
    )

    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    print(f"Loading documents from: {args.input_dir}")
    file_extractor = {".pdf": PyMuPDFReader()}
    documents = SimpleDirectoryReader(args.input_dir, file_extractor=file_extractor).load_data()
    print(f"Loaded {len(documents)} documents.")

    ollama_base_url = f"http://{args.host}:11434"
    Settings.embed_model = OllamaEmbedding(
        model_name=args.embed_model,
        base_url=ollama_base_url,
    )
    Settings.llm = None

    print("Creating vector store index...")
    index = VectorStoreIndex.from_documents(
        documents,
        show_progress=True,
    )
    print("Vector store index created.")

    # Sanitize model name for directory use
    model_name_sanitized = args.embed_model.replace(":", "_").replace("/", "_")
    final_output_dir = os.path.join(args.output_dir, model_name_sanitized)
    os.makedirs(final_output_dir, exist_ok=True)

    print(f"Persisting vector store to: {final_output_dir}")
    index.storage_context.persist(persist_dir=final_output_dir)
    print("Vector store persisted successfully.")

if __name__ == "__main__":
    main()
