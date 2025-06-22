#!/bin/bash
# See: https://hub.docker.com/r/ollama/ollama

# We need a username as we will use the home directory
username="$1"
if [ -z "$username" ]; then
    echo "Usage: $0 <username>"
    exit 1
fi

ollama_container_name="ollama-gpu"
ollama_data_volume="/home/$username/ollama_data"
ollama_image="ollama/ollama"
ollama_port="11434"
ollama_model="qwen2.5:72b"
network_name="mcp-net"

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
docker run -d --gpus "device=0" -v "$ollama_data_volume:/root/.ollama" --network="$network_name" -p "$ollama_port:$ollama_port" --name "$ollama_container_name" "$ollama_image" > /dev/null

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

exit 0