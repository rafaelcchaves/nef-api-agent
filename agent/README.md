# NEF API Agent

This directory contains the core logic for the NEF API Agent, a LlamaIndex-based application designed to interact with a 5G Network Exposure Function (NEF).

## Purpose

The agent leverages a large language model (LLM), typically running on Ollama, to intelligently manage 5G network traffic. Its primary function is to analyze network performance metrics (such as jitter and throughput) and make informed decisions about routing traffic between the traditional Internet path and a Multi-access Edge Computing (MEC) path. This aims to optimize network performance and user experience.

## Getting Started with the Agent

To run the NEF API Agent, follow these steps:

### 1. Install Dependencies

Ensure you have Python 3 installed. It's highly recommended to use a virtual environment to manage dependencies.

First, create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Then, install the agent's Python dependencies listed in `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 2. Required Services

The agent relies on external services to function:

*   **Ollama Instance:** A running Ollama instance is required to host the large language model that the agent uses for decision-making. You can find installation and setup instructions on the [Ollama website](https://ollama.ai/).
*   **5G Core Network with NEF:** The agent interacts with a 5G core network, specifically its Network Exposure Function (NEF). Ensure you have a compatible 5G core network running. For this repository, the `free5gc` submodule provides a Docker-based Free5GC core network. Refer to the `free5gc` submodule's documentation for setup instructions.
*   **MCP Endpoint:** The agent expects an MCP (Multi-access Edge Computing Platform) endpoint to be accessible at a configured address. This endpoint provides the tools that the agent utilizes. You will need to start this server separately.

### 3. How to Start the MCP Server

The MCP server is located in the `agent/mcp` directory. To start it:

1.  Navigate to the `agent/mcp` directory:
    ```bash
    cd agent/mcp
    ```
2.  (Optional but recommended) If you are not already in your main virtual environment, create and activate a new one for the MCP server:
    ```bash
    python3 -m venv .venv_mcp
    source .venv_mcp/bin/activate
    ```
3.  Install the MCP server's dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  Run the MCP server:
    ```bash
    python mcp-server.py
    ```
    You can specify the NEF URL if it's different from the default (which can be found in `agent/mcp/mcp-server.py`):
    ```bash
    python mcp-server.py --nef-url <your_nef_url>
    ```
### 4. Run the Agent

Once the dependencies are installed and the required services (Ollama, 5G Core with NEF, and MCP endpoint) are running, you can start the agent from the main `agent/` directory:

```bash
source .venv/bin/activate # Activate your agent's virtual environment if not already active
python main.py
```

You can customize the Ollama model and host, and the MCP server URL using command-line arguments:

```bash
python main.py --model <model_name> --host <ollama_host> --mcp-server <mcp_server_url> --thinking
```

**Example:**

```bash
python main.py --model llama3.2:latest --host localhost --mcp-server http://localhost:8080/sse
```