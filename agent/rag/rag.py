from typing import List
import os
from llama_index.core import StorageContext, load_index_from_storage, Settings
from llama_index.core.tools import FunctionTool
from llama_index.core.response_synthesizers import ResponseMode
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama

class RAGPipeline:
    def __init__(self, 
                 host: str = "localhost", 
                 llm_model: str = "qwen3:1.7b", 
                 embed_model: str = "all-minilm:latest",
                 vector_store_dir: str = "rag/vector_store",
                 top_k: int = 6):
        
        self.ollama_base_url = f"http://{host}:11434"
        self.llm_model_name = llm_model
        self.embed_model_name = embed_model
        self.vector_store_dir = vector_store_dir
        self.top_k = top_k
        self.query_engine = None
        
        self._initialize()

    def _initialize(self):
        # Sanitize model name for directory use, matching creation logic
        model_name_sanitized = self.embed_model_name.replace(":", "_").replace("/", "_")
        final_vector_store_dir = os.path.join(self.vector_store_dir, model_name_sanitized)

        if not os.path.exists(final_vector_store_dir):
            raise FileNotFoundError(f"Vector store directory not found at {final_vector_store_dir}")

        self.llm = Ollama(
            model=self.llm_model_name,
            keep_alive="1m",
            base_url=self.ollama_base_url,
            thinking=False,
            temperature=0.3,
            request_timeout=120.0,
            context_window=4096,
            num_predict=256,
            top_p=0.8,
            top_k=20,
            min_p=0,
            presence_penalty=1.0
        )
        
        self.embed_model = OllamaEmbedding(
            model_name=self.embed_model_name,
            base_url=self.ollama_base_url,
        )

        # Set the global embedding model for LlamaIndex
        Settings.embed_model = self.embed_model

        storage_context = StorageContext.from_defaults(persist_dir=final_vector_store_dir)
        index = load_index_from_storage(storage_context)
        
        self.query_engine = index.as_query_engine(
            llm=self.llm,
            embed_model=self.embed_model,
            similarity_top_k=self.top_k,
            response_mode=ResponseMode.SIMPLE_SUMMARIZE
        )

    def query(self, query_str: str) -> str:
        """
        Queries the RAG pipeline with the given query string.
        """
        if not self.query_engine:
            return "RAG Pipeline not initialized."
        
        response = self.query_engine.query(query_str)
        return str(response)

    def get_subscription_schema(self) -> dict:
        """
        Retrieves the JSON schema for a 5G Traffic Influence subscription.
        Use this tool to understand the required structure and fields when creating or updating subscriptions.
        """
        return {
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

    def get_tools(self) -> List[FunctionTool]:
        """
        Returns a list of LlamaIndex FunctionTools provided by the RAG pipeline.
        """
        search_tool = FunctionTool.from_defaults(
            fn=self.query,
            name="search_documentation",
            description="Useful for searching technical documentation and specifications related to NEF and 5G APIs. Use this tool when you need specific details about API endpoints, data structures, or 3GPP specifications."
        )
        schema_tool = FunctionTool.from_defaults(
            fn=self.get_subscription_schema,
            name="get_subscription_schema",
            description="Retrieves the JSON schema for 5G Traffic Influence subscriptions. Use this to understand the required structure and fields when constructing a subscription payload for tools like 'add_subscription'."
        )
        return [search_tool, schema_tool]
