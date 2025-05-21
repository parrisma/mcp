#!/bin/bash

# Default values
force_rebuild=false
image_name="mcp-dev"
container_name="mcp-dev"
network_name="mcp-net"

# Display help message
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo "Run a development container with configurable settings."
    echo
    echo "Options:"
    echo "  -f                Force rebuild of the Docker image"
    echo "  -i IMAGE_NAME     Set the Docker image name (default: mcp-dev)"
    echo "  -c CONTAINER_NAME Set the container name (default: mcp-dev)"
    echo "  -n NETWORK_NAME   Set the Docker network name (default: mcp-net)"
    echo "  -h                Display this help message and exit"
    echo
}

# Parse command-line flags
while getopts "fi:c:n:h" opt; do
    case $opt in
        f)
            force_rebuild=true
        ;;
        i)
            image_name="$OPTARG"
        ;;
        c)
            container_name="$OPTARG"
        ;;
        n)
            network_name="$OPTARG"
        ;;
        h)
            show_help
            exit 0
        ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            show_help
            exit 1
        ;;
    esac
done

# Check if the container is running
if docker ps --filter "name=$container_name" --format "{{.ID}}" | grep -q .; then
    
    # Container is running, stop it
    echo "Stopping $container_name container..."
    docker stop "$container_name"
    sleep 5
    
    # Remove the container
    echo "Removing $container_name container..."
    docker rm "$container_name"
    sleep 15
    echo "Removed $container_name container..."
else
    echo "$container_name container is not running."
fi

# Check if docker group exists
if ! getent group docker > /dev/null; then
    echo "Error: docker group does not exist. Please create it first."
    exit 1
fi
HOST_DOCKER_GID=$(getent group docker | cut -d: -f3)
echo "Found docker group with GID: ${HOST_DOCKER_GID}"

# Check if mcp-dev group exists.
# This assumes that there is a user and group called mcp-dev, these are created inside the container
# such that when we mound the the local dev folders the development inside the container and outside the container
# can manipulate the same files
#
# The idea is that this container is remote attached to by vscode, such that all development is done inside the container
# and all developers have consistent development environments.
#
if ! getent group mcp-dev > /dev/null; then
    echo "Error: mcp-dev group does not exist. Please create it first."
    exit 1
fi
HOST_MCP_DEV_GID=$(getent group mcp-dev | cut -d: -f3)
echo "Found mcp-dev group with GID: ${HOST_MCP_DEV_GID}"

# Check if mcp-dev user exists
if ! id mcp-dev &>/dev/null; then
    echo "Error: mcp-dev user does not exist. Please create it first."
    exit 1
fi
HOST_MCP_DEV_UID=$(id -u mcp-dev)
echo "Found mcp-dev user with UID: ${HOST_MCP_DEV_UID}"

# Check if the image exists locally
if $force_rebuild || ! docker images -q "${image_name}:latest" > /dev/null; then
    echo "Building ${image_name}:latest image..."
    docker build \
    --build-arg DOCKER_GID=${HOST_DOCKER_GID} \
    --build-arg MCP_DEV_GID=${HOST_MCP_DEV_GID} \
    --build-arg MCP_DEV_UID=${HOST_MCP_DEV_UID} \
    -t "${image_name}:latest" .
    if [ $? -ne 0 ]; then
        echo "Failed to build ${image_name}:latest image."
        exit 1
    fi
else
    echo "${image_name}:latest image found locally."
fi

# Check if network exists, create it if it doesn't
if ! docker network ls | grep -q "$network_name"; then
    echo "Creating $network_name network..."
    docker network create "$network_name"
    if [ $? -ne 0 ]; then
        echo "Failed to create $network_name network."
        exit 1
    fi
    echo "Created $network_name network."
else
    echo "$network_name network already exists."
fi

# This command starts a new Docker container, so it can be attached to by vscode
#
# --rm: Automatically remove container on exit
# --name: Assign the specified name to the container, this is needed to attach to it from vscode
# -d: Run the container in the background (detached mode)
# -v: Mount directories from the host into the container
#     - First mount: Project files from host to container
#     - Second mount: Docker socket to allow Docker commands from inside the container
# --network: Connect the container to the specified Docker network
#     - This allows the container to communicate with other containers on the same network
#     - This allows the tests to run inside the container to communicate with the host
# --user: Run the container with the specified user and group IDs
# tail -f /dev/null: A simple command that keeps the container running indefinitely
docker run --rm --name "$container_name" -d \
-v "$(pwd)/../..":/mcp \
-v /var/run/docker.sock:/var/run/docker.sock \
--network="$network_name" \
--user ${HOST_MCP_DEV_UID}:${HOST_DOCKER_GID} \
"${image_name}:latest" tail -f /dev/null
