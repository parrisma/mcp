#!/bin/bash
# See: https://github.com/open-webui/open-webui

# We need a username as we will use the home directory
username="$1"
if [ -z "$username" ]; then
    echo "Usage: $0 <username>"
    exit 1
fi

openwebui_container_name="open-webui"
openwebui_data_volume="/home/$username/openwebui_data"
openwebui_volume_mount="/app/backend/data"
openwebui_image="ghcr.io/open-webui/open-webui:cuda"
openwebui_port="3000"
ollama_base_url="http://localhost:11434"
network_name="mcp-net"

echo "##################################################################################"
echo "# Script will do the following:                                                   "
echo "#                                                                                 "
echo "# 1. Check if Open WebUI container exists, if so, stop and remove it             "
echo "# 2. Create directory for Open WebUI persistent storage volume, if it does not exist"
echo "# 3. Start Open WebUI container with GPU support                                 "
echo "#                                                                                 "
echo "##################################################################################"

echo
echo "##################################    1    #######################################"
echo
echo "> Setting up Open WebUI Container, assumes you have GPU support"
echo "> Checking if Open WebUI container [$openwebui_container_name] exists..."
docker_res=$(docker ps -a --filter name="$openwebui_container_name" --format "{{.Names}}")
if [ "$docker_res" = "$openwebui_container_name" ]; then
    echo "> Open WebUI container ['$openwebui_container_name'] exists, going to stop and remove it so we have a clean environment."
    echo "> Stopping container..."
    docker stop $openwebui_container_name > /dev/null
    echo "> Removing container..."
    docker rm $openwebui_container_name > /dev/null
    echo "> Container clean up done"
else
    echo "> Open WebUI container [$openwebui_container_name] does not exist, will create and start one"
fi

echo
echo "##################################    2    #######################################"
echo
echo "> Setting up Open WebUI persistent storage volume"
if [ ! -d "$openwebui_data_volume" ]; then
    echo "> Creating [$openwebui_data_volume] directory as Open WebUI persistent storage volume"
    mkdir -p "$openwebui_data_volume"
    if [ $? -ne 0 ]; then
        echo "> Error creating directory ['$openwebui_data_volume']"
        exit 1
    fi
    echo "> Setting read/write permissions for [$openwebui_data_volume] for owner and group"
    chmod 660 "$openwebui_data_volume"
else
    echo "> Open WebUI persistent volume [$openwebui_data_volume] exists already"
fi

echo
echo "##################################    3    #######################################"
echo
echo "> Starting Open WebUI container..."
echo "> docker run -d --network=host -p \"$openwebui_port:8080\" --gpus all -v \"$openwebui_data_volume:$openwebui_volume_mount\" -e OLLAMA_BASE_URL=\"$ollama_base_url\" --name \"$openwebui_container_name\" \"$openwebui_image\""
docker run -d --network=host -p "$openwebui_port:8080" --gpus all -v "$openwebui_data_volume:$openwebui_volume_mount" -e OLLAMA_BASE_URL="$ollama_base_url" --name "$openwebui_container_name" "$openwebui_image" > /dev/null

echo "> Waiting for Open WebUI container to be running..."
tries=0
while [[ "$tries" -lt "10" ]]; do
    tries=$((tries + 1))
    if docker inspect --format='{{.State.Running}}' "$openwebui_container_name" 2>/dev/null | grep -q 'true'; then
        echo "> Container ['$openwebui_container_name'] started, OK."
        echo "> Open WebUI is available at: http://localhost:$openwebui_port"
        break
    else
        echo "> Container ['$openwebui_container_name'] is not yet running. Retrying in 2 seconds..."
        sleep 2
    fi
done

# Check if container is actually running
docker_res=$(docker ps -a --filter name="$openwebui_container_name" --format "{{.Names}}")
if [ "$docker_res" = "$openwebui_container_name" ]; then
    echo "> Open WebUI container [$openwebui_container_name] is running successfully"
    echo "> You can access the web interface at: http://localhost:$openwebui_port"
else
    echo "> Open WebUI container [$openwebui_container_name] failed to start, exiting"
    exit 1
fi

exit 0