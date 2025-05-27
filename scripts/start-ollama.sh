#!/bin/bash
# See: https://hub.docker.com/r/ollama/ollama

# --- Default values ---
DEFAULT_OLLAMA_CONTAINER_NAME="ollama-gpu"
DEFAULT_OLLAMA_IMAGE="ollama/ollama"
DEFAULT_OLLAMA_PORT="11434"
DEFAULT_OLLAMA_MODEL="qwen2.5:72b"

# --- Initialize variables with defaults ---
ollama_container_name="$DEFAULT_OLLAMA_CONTAINER_NAME"
ollama_image="$DEFAULT_OLLAMA_IMAGE"
ollama_port="$DEFAULT_OLLAMA_PORT"
ollama_model="$DEFAULT_OLLAMA_MODEL"

# --- Usage function ---
usage() {
    echo "Usage: $0 <username> [options]"
    echo ""
    echo "Manages and starts an Ollama Docker container."
    echo ""
    echo "Positional arguments:"
    echo "  <username>          (Required) The username for constructing the data volume path (/home/<username>/ollama_data)."
    echo ""
    echo "Options:"
    echo "  --container-name <name>  Name for the Ollama Docker container (default: \"$DEFAULT_OLLAMA_CONTAINER_NAME\")."
    echo "  --image <image>          Docker image for Ollama (default: \"$DEFAULT_OLLAMA_IMAGE\")."
    echo "  --port <port>            Port to map for the Ollama service (default: $DEFAULT_OLLAMA_PORT)."
    echo "  --model <model_tag>      Ollama model to pull and run (default: \"$DEFAULT_OLLAMA_MODEL\")."
    echo "  -h, --help               Show this help message."
    exit 1
}

# --- Argument parsing ---
# First argument is mandatory username
if [ $# -lt 1 ] || [ -z "$1" ] || [ "$1" = "-h" ] || [ "$1" = "-?" ]|| [ "$1" = "--help" ]; then
    usage
fi
username="$1"
shift # Remove username from argument list

# Optionally, check if user exists on the system
if ! id "$username" &>/dev/null; then
    echo "Error: Given user ['$username'] does not exist on this system."
    exit 1
fi

# Parse options
DEFAULT_OLLAMA_NETWORK="mcp-net"
ollama_network="$DEFAULT_OLLAMA_NETWORK"

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --container-name) ollama_container_name="$2"; shift ;;
        --image) ollama_image="$2"; shift ;;
        --port) ollama_port="$2"; shift ;;
        --model) ollama_model="$2"; shift ;;
        --network) ollama_network="$2"; shift ;;
        -h|--help) usage ;;
        *) echo "Unknown parameter passed: $1"; usage ;;
    esac
    shift
done

# --- Derived variables ---
ollama_data_volume="/home/$username/ollama_data" # This still depends on the positional username

echo "------------------- Configuration -------------------"
echo "Ollama container name : $ollama_container_name"
echo "Ollama image          : $ollama_image"
echo "Ollama port           : $ollama_port"
echo "Ollama model          : $ollama_model"
echo "Ollama data volume    : /home/$username/ollama_data"
echo "Ollama network        : $ollama_network"
echo "-----------------------------------------------------"

# --- Script logic continues below with the configured variables ---

echo "##################################################################################"
echo "# Script will do the following:                                                   "
echo "#                                                                                 "
echo "# 1. Check if Ollama container exists, if so, stop and remove it                  "
echo "# 2. Create directory for Ollama persistent storage volume, if it does not exist  "
echo "# 3. Start Ollama container with GPU support                                      "
echo "# 4. Ask the Ollama container to load and run the llm model $ollama_model         "
echo "#                                                                                 "
echo "##################################################################################"

echo
echo "##################################    1    #######################################"
echo
echo "> Setting up Ollama Container, assumes you have GPU support"
echo "> Checking if Ollama container [$ollama_container_name] exists..."
docker_res=$(docker ps -a --filter name="$ollama_container_name" --format "{{.Names}}")
if [ "$docker_res" = "$ollama_container_name" ]; then
    echo "> Ollama container ['$ollama_container_name'] exists, going to stop and remove it so we have a clean environment."
    echo "> Stopping container..."
    docker stop $ollama_container_name > /dev/null
    echo "> Removing container..."
    docker rm $ollama_container_name > /dev/null
    echo "> Container clean up done"
else
    echo "> Ollama container [$ollama_container_name] does not exist, will create and start one"
fi

echo
echo "##################################    2    #######################################"
echo
echo "> Setting up Ollama persistent storage volume"
if [ ! -d "$ollama_data_volume" ]; then
    echo "> Creating [$ollama_data_volume] directory as Ollama persistent storage volume"
    mkdir -p "$ollama_data_volume"
    if [ $? -ne 0 ]; then
        echo "> Error creating directory ['$ollama_data_volume']"
        exit 1
    fi
    echo "> Setting read/write permissions for [$ollama_data_volume] for owner and group"
    chmod 660 "$ollama_data_volume"
else
    echo "> Ollama persistent volume [$ollama_data_volume] exists already"
fi

echo
echo "##################################    3    #######################################"
echo
echo "> Starting Ollama container..."
docker run -d --gpus "device=0" -v "$ollama_data_volume:/root/.ollama" -p "$ollama_port:$ollama_port" --network "$ollama_network" --name "$ollama_container_name" "$ollama_image" > /dev/null

echo "> Waiting for Ollama container to be running..."
tries=0
while [[ "$tries" -lt "10" ]]; do
    tries=$((tries + 1))
    if docker inspect --format='{{.State.Running}}' "$ollama_container_name" 2>/dev/null | grep -q 'true'; then
        echo "> Container ['$ollama_container_name'] started, OK."
        break
    else
        echo "> Container ['$ollama_container_name'] is not yet running. Retrying in 2 seconds..."
        sleep 2
    fi
done

echo
echo "##################################    4    #######################################"
echo
docker_res=$(docker ps -a --filter name="$ollama_container_name" --format "{{.Names}}")
if [ "$docker_res" = "$ollama_container_name" ]; then
    echo "> Asking ['$ollama_container_name'] to start Ollama model [$ollama_model]"
    docker exec "$ollama_container_name" ollama run "$ollama_model" > /dev/null
else
    echo "> Ollama container [$ollama_container_name] failed to start, exiting"
    exit 1
fi

echo "> Waiting for [$ollama_model] to be running..."
tries=0
while [[ "$tries" -lt "10" ]]; do
    tries=$((tries + 1))
    if docker exec "$ollama_container_name" ollama ps 2>/dev/null | grep -q "$ollama_model"; then
        echo "> Model ['$ollama_model'] started."
        break
    else
        echo "> Model ['$ollama_model'] is not yet started. Retrying in 2 seconds..."
        sleep 2
    fi
done

