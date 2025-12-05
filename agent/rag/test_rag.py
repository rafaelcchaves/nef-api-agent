import argparse
import sys
import os
import time
import tiktoken
from llama_index.core import StorageContext, load_index_from_storage, Settings
from llama_index.core.callbacks import CallbackManager, TokenCountingHandler
from llama_index.core.response_synthesizers import ResponseMode
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama

DEFAULT_VECTOR_STORE_DIR = "vector_store"

def main():
    parser = argparse.ArgumentParser(description="Retrieve and print nodes from the vector store.")
    parser.add_argument(
        "query",
        type=str,
        help="The query string to retrieve nodes for.",
    )
    parser.add_argument(
        "-e",
        "--embed-model",
        type=str,
        default="qwen3-embedding:0.6b", # Changed default embedding model
        help="The name of the Ollama embedding model to use (default: 'qwen3-embedding:1.7b').",
    )
    parser.add_argument(
        "-m",
        "--model",
        type=str,
        default="qwen3:1.7b",
        help="The name of the Ollama LLM model to use (default: 'qwen3:1.7b').",
    )
    parser.add_argument(
        "-H",
        "--host",
        type=str,
        default="localhost",
        help="The host for the Ollama instance (default: 'localhost').",
    )
    parser.add_argument(
        "-k",
        "--top-k",
        type=int,
        default=3,
        help="Number of nodes to retrieve (default: 3).",
    )

    args = parser.parse_args()

    # Sanitize model name for directory use
    model_name_sanitized = args.embed_model.replace(":", "_").replace("/", "_")
    final_vector_store_dir = os.path.join(DEFAULT_VECTOR_STORE_DIR, model_name_sanitized)

    if not os.path.exists(final_vector_store_dir):
        print(f"Error: Vector store directory not found at {final_vector_store_dir}")
        sys.exit(1)

    # Setup Token Counting
    token_counter = TokenCountingHandler(
        tokenizer=tiktoken.get_encoding("cl100k_base").encode
    )
    Settings.callback_manager = CallbackManager([token_counter])

    ollama_base_url = f"http://{args.host}:11434"
    Settings.llm = Ollama(
        model=args.model,
        keep_alive = "1m",
        base_url=ollama_base_url,
        thinking = False,
        temperature = 0.3,
        request_timeout=120.0,
        context_window=4096,
        num_predict=256,
        top_p=0.8,
        top_k=20,
        min_p=0,
        presence_penalty=1.0
    )
    Settings.embed_model = OllamaEmbedding(
        model_name=args.embed_model,
        base_url=ollama_base_url,
    )
    
    try:
        storage_context = StorageContext.from_defaults(persist_dir=final_vector_store_dir)
        index = load_index_from_storage(storage_context)
    except Exception as e:
        print(f"Failed to load index: {e}")
        sys.exit(1)

    query_engine = index.as_query_engine(
        similarity_top_k=args.top_k,
        response_mode=ResponseMode.SIMPLE_SUMMARIZE
    )

    token_counter.reset_counts() # Reset before query
    start_time = time.time()
    response = query_engine.query(args.query)
    end_time = time.time()

    print(f"\nResponse:\n{response}\n")

    # Calculate metrics
    processing_time = end_time - start_time

    print("=" * 40)
    print("METRICS")
    print("=" * 40)
    print(f"Processing Time:       {processing_time:.4f} seconds")
    print(f"Retrieved Nodes:       {len(response.source_nodes)}")
    print(f"Embedding Tokens:      {token_counter.total_embedding_token_count}")
    print(f"LLM Prompt Tokens:     {token_counter.prompt_llm_token_count}")
    print(f"LLM Completion Tokens: {token_counter.completion_llm_token_count}")
    print(f"Total LLM Token Count: {token_counter.total_llm_token_count}")
    print("=" * 40)

if __name__ == "__main__":
    main()
