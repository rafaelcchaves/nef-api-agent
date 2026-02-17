# NEF API Agent Repository

This repository contains the necessary components to run a 5G core network and an agent for interacting with it.

## 5G Core Initialization (Free5GC)

This section describes the process of initializing the 5G core network (Free5GC).

**Note:** Make sure you have Docker Engine and Docker Compose installed and configured on your system before proceeding.

### Step 1: Download Submodules

If not done yet, clone the repository and initialize the submodules:

```bash
git clone https://github.com/rafaelcchaves/nef-api-agent.git
cd nef-api-agent
git submodule update --init --recursive
```

### Step 2: Install the GTP5G Module

The gtp5g module is required to handle GTP packets in the 5G data plane. Follow the instructions in `gtp5g/README.md` for complete installation.

### Step 3: Initialize the 5G Core

With the prerequisites met, start the 5G core using Docker Compose:

```bash
cd free5gc
docker compose pull
docker compose -f docker-compose-ulcl.yaml up -d
```

The `-d` parameter runs containers in detach mode (background). To view logs in real time, omit this parameter or use:

```bash
docker compose -f docker-compose-ulcl.yaml logs -f
```

### Step 4: Create UE via WebConsole

Access the Free5GC web interface to create a subscriber (UE):

1. Access: `http://localhost:5000`
2. Follow the official guide starting from step 4: https://free5gc.org/guide/Webconsole/Create-Subscriber-via-webconsole/

Fill in the necessary information for the UE, including IMSI, key, and other subscriber parameters.

### Step 5: Connect UE to gNodeB via UERANSIM

With the core running and the UE created, connect the UE to the network using UERANSIM:

```bash
# Access the UERANSIM container
docker exec -it ueransim bash

# Connect the UE
./nr-ue -c config/uecfg.yaml
```

### Step 6: Verify Connectivity

In a new terminal, check the network interface created by UERANSIM:

```bash
docker exec -it ueransim bash

# View network interfaces
ip -br a
```

To verify the route configured for the UE and test connectivity:

```bash
# Install traceroute (if necessary)
apt update && apt install -y traceroute

# Test connectivity replacing:
# <ueransim_interface> with the interface shown by ip -br a
# <target_ip> with the desired destination IP address
traceroute -i <ueransim_interface> <target_ip>
```

## NEF API Agent

The agent leverages a large language model (LLM) to intelligently manage 5G network traffic using the 3GPP Traffic Influence API. It processes natural language requests and autonomously executes operations on the NEF, including creating, reading, updating, and deleting traffic influence subscriptions. The agent can use either local models (via Ollama) or Anthropic Claude models.

### Prerequisites

Before running the agent, ensure you have the following services running:

* **LLM Provider:** The agent automatically selects the provider based on the model name:
  * **Ollama** for local models (e.g., `qwen3:4b`, `gpt-oss:20b`). Installation and setup instructions are available on the [Ollama website](https://ollama.ai/).
  * **Anthropic Claude** for models starting with `claude` (e.g., `claude-sonnet-4-5-20251101`, `claude-opus-4-5-20251101`). Requires `ANTHROPIC_API_KEY` in your `.env` file.
* **5G Core Network with NEF:** The agent interacts with a 5G core network, specifically its Network Exposure Function (NEF). Ensure you have a compatible 5G core network running. For this repository, the `free5gc` submodule provides a Docker-based Free5GC core network.
* **MCP Endpoint:** The agent expects an MCP (Model Context Protocol) endpoint to be accessible at a configured address. This endpoint provides the tools that the agent utilizes.

### Step 1: Install Dependencies

Navigate to the `agent/` directory and create a virtual environment:

```bash
cd agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Step 2: Environment Variables

For Claude model support, create a `.env` file in the `agent/` directory with your Anthropic API key:

```bash
ANTHROPIC_API_KEY=your_api_key_here
```

### Step 3: Start MCP Server

The MCP server is located in the `agent/mcp` directory and uses FastMCP to expose NEF API tools. To start it:

1. Navigate to the `agent/mcp` directory:
   ```bash
   cd agent/mcp
   ```
2. (Optional but recommended) Create and activate a virtual environment for the MCP server:
   ```bash
   python3 -m venv .venv_mcp
   source .venv_mcp/bin/activate
   ```
3. Install the MCP server's dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the MCP server:
   ```bash
   python mcp-server.py
   ```
   You can specify the NEF URL if it's different from the default (`http://10.100.200.6:8000`):
   ```bash
   python mcp-server.py --nef-url <your_nef_url>
   ```

**Available MCP Tools:**

* `list_subscriptions` - Retrieve all active subscriptions for an AF
* `add_subscription` - Create a new subscription
* `get_subscription_details` - Read a specific subscription
* `update_full_subscription` - Fully update/replace a subscription
* `update_partial_subscription` - Partially update a subscription
* `remove_subscription` - Delete a subscription

> **Note:** You can use the [MCP Inspector](https://github.com/modelcontextprotocol/inspector) to debug and test the MCP server. Run `DANGEROUSLY_OMIT_AUTH=true npx @modelcontextprotocol/inspector http://localhost:8080/sse` to inspect available tools and test them interactively.

### Step 4: Run the Agent

With the MCP server running, execute the agent from the `agent/` directory:

```bash
cd agent
source .venv/bin/activate
python main.py "<your_query>"
```

**Command-Line Arguments:**

| Option | Description | Default |
|--------|-------------|---------|
| `-m, --model` | Model to use (Ollama or Claude) | `qwen3:4b` |
| `-H, --host` | Ollama host (ignored for Claude models) | `localhost` |
| `-M, --mcp-server` | MCP server URL | `http://localhost:8080/sse` |
| `--context_insertion` | Include schema in system prompt | - |
| `-s, --streaming` | Enable streaming response | - |
| `query` | The query to process (required) | - |

**Usage:**

```bash
python3 main.py [OPTIONS] query
```

Where `query` is the natural language request to be processed by the agent.
