#!/bin/bash

# Need compatiable python chromadb version: pip show chromadb = version: 1.0.13

chroma_container_name="chromadb"
chroma_data_volume="./chroma_data"
chroma_image="chromadb/chroma:1.0.8.dev35"
chroma_port="8000"
network_name="mcp-net"

echo "##################################################################################"
echo "# Script will do the following:                                                   "
echo "#                                                                                 "
echo "# 1. Check if ChromaDB container exists, if so, stop and remove it                "
echo "# 2. Create directory for ChromaDB persistent storage volume, if it does not exist"
echo "# 3. Start ChromaDB container                                                     "
echo "#                                                                                 "
echo "##################################################################################"

echo
echo "##################################    1    #######################################"
echo
echo "> Setting up ChromaDB Container"
echo "> Checking if ChromaDB container [$chroma_container_name] exists..."
docker_res=$(docker ps -a --filter name="$chroma_container_name" --format "{{.Names}}")
if [ "$docker_res" = "$chroma_container_name" ]; then
    echo "> ChromaDB container ['$chroma_container_name'] exists, going to stop and remove it so we have a clean environment."
    echo "> Stopping container..."
    docker stop $chroma_container_name > /dev/null
    echo "> Removing container..."
    docker rm $chroma_container_name > /dev/null
    echo "> Container clean up done"
else
    echo "> ChromaDB container [$chroma_container_name] does not exist, will create and start one"
fi

echo
echo "##################################    2    #######################################"
echo
echo "> Setting up ChromaDB Container"
echo "> Checking if ChromaDB container [$chroma_container_name] exists..."
docker_res=$(docker ps -a --filter name="$chroma_container_name" --format "{{.Names}}")
if [ "$docker_res" = "$chroma_container_name" ]; then
    echo "> ChromaDB container ['$chroma_container_name'] exists, going to stop and remove it so we have a clean environment."
    echo "> Stopping container..."
    docker stop $chroma_container_name > /dev/null
    echo "> Removing container..."
    docker rm $chroma_container_name > /dev/null
    echo "> Container clean up done"
else
    echo "> ChromaDB container [$chroma_container_name] does not exist, will create and start one"
fi

echo
echo "##################################    3    #######################################"
echo
echo "> Current working directory: $(pwd)"
echo "> Setting up ChromaDB persistent storage volume"
if [ ! -d "$chroma_data_volume" ]; then
    echo "> Creating [$chroma_data_volume] directory as ChromaDB persistent storage volume"
    mkdir -p "$chroma_data_volume"
    if [ $? -ne 0 ]; then
        echo "> Error creating directory ['$chroma_data_volume']"
        exit 1
    fi
    echo "> Setting read/write permissions for [$chroma_data_volume] for owner and group"
    chmod 660 "$chroma_data_volume"
else
    echo "> ChromaDB persistent volume [$chroma_data_volume] exists already"
fi

echo
echo "##################################    4    #######################################"
echo
echo "> Starting ChromaDB container..."

docker run -d \
  --name chromadb \
  --network="$network_name" \
  -p "$chroma_port:$chroma_port" \
  -v "$chroma_data_volume:/chroma/chroma" \
  -e IS_PERSISTENT=TRUE \
  -e PERSIST_DIRECTORY=/chroma/chroma \
  "$chroma_image" > /dev/null

echo "> Waiting for ChromaDB container to be running..."
tries=0
while [[ "$tries" -lt "10" ]]; do
    tries=$((tries + 1))
    if docker inspect --format='{{.State.Running}}' "$chroma_container_name" 2>/dev/null | grep -q 'true'; then
        echo "> Container ['$chroma_container_name'] started, OK."
        break
    else
        echo "> Container ['$chroma_container_name'] is not yet running. Retrying in 2 seconds..."
        sleep 2
    fi
done
