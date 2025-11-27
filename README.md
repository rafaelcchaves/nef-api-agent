# NEF API Agent Repository

This repository contains the necessary components to run a 5G core network and an agent for interacting with it.

## Repository Setup

This repository includes git submodules. To ensure the repository is correctly set up, you must initialize and update the submodules. After cloning the repository, run the following command:

```bash
git submodule update --init --recursive
```

This will fetch the necessary submodule contents.

## Directory Purpose

The repository is organized into the following main directories:

*   `agent/`: This directory holds the source code for the NEF API agent. The agent is designed to interact with the 5G core's Network Exposure Function (NEF) to manage network traffic. For detailed instructions on setting up and running the agent, including dependency management with a virtual environment, refer to `agent/README.md`.

*   `free5gc/`: This is a git submodule that contains a Docker-based implementation of the Free5GC core network. This provides the fundamental 5G network functions.

*   `gtp5g/`: This git submodule contains the gtp5g kernel module, which is required for handling GPRS Tunnelling Protocol (GTP) packets in the 5G data plane.