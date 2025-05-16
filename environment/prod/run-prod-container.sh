#!/bin/bash

# Default values
IMAGE_NAME="mcp-prod"
CONTAINER_NAME="mcp-prd-svc"
HOST="0.0.0.0"
PORT="6277"  # External port that will be mapped to the container
INTERNAL_PORT="6277"  # Internal container port where the MCP server listens

# Display usage information
function show_usage {
    echo "Usage: $0 [OPTIONS]"
    echo "Run the MCP production container with configurable options."
    echo ""
    echo "Options:"
    echo "  -i, --image NAME       Set the image name/tag (default: $IMAGE_NAME)"
    echo "  -n, --name NAME        Set the container name (default: $CONTAINER_NAME)"
    echo "  --host HOST            Set the host to bind to (default: $HOST)"
    echo "  -p, --port PORT        Set the external port to bind to (default: $PORT)"
    echo "  --internal-port PORT   Set the internal container port (default: $INTERNAL_PORT)"
    echo "  -h, --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --image custom-mcp"
    echo "  $0 --host 127.0.0.1 --port 8080"
    echo "  $0 --port 8080 --internal-port 9000"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -i|--image)
            IMAGE_NAME="$2"
            shift 2
            ;;
        -n|--name)
            CONTAINER_NAME="$2"
            shift 2
            ;;
        --host)
            HOST="$2"
            shift 2
            ;;
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        --internal-port)
            INTERNAL_PORT="$2"
            shift 2
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Display run configuration
echo "Running MCP production container with the following configuration:"
echo "  Image name:     $IMAGE_NAME"
echo "  Container name: $CONTAINER_NAME"
echo "  Host:           $HOST"
echo "  External port:  $PORT (mapped to container's internal port $INTERNAL_PORT)"
echo ""

# Check if a container with the same name is already running
RUNNING_CONTAINER=$(docker ps -q -f name="$CONTAINER_NAME")
if [ -n "$RUNNING_CONTAINER" ]; then
    echo "Container with name '$CONTAINER_NAME' is already running. Stopping it..."
    docker stop "$CONTAINER_NAME" > /dev/null
    echo "Container stopped."
fi

# Check if a stopped container with the same name exists
EXISTING_CONTAINER=$(docker ps -a -q -f name="$CONTAINER_NAME")
if [ -n "$EXISTING_CONTAINER" ]; then
    echo "Container with name '$CONTAINER_NAME' exists. Removing it..."
    docker rm "$CONTAINER_NAME" > /dev/null
    echo "Container removed."
fi

# Check if the mcp-net network exists
echo "Checking if Docker network 'mcp-net' exists..."
if ! docker network ls | grep -q "mcp-net"; then
    echo "Error: Docker network 'mcp-net' does not exist."
    echo "Please create the network with: docker network create mcp-net"
    exit 1
fi
echo "Network 'mcp-net' found."

# Run the Docker container as a daemon
echo "Starting container as daemon..."
# The format for port mapping is: -p <external-port>:<internal-port>
# The MCP_PORT environment variable must match the internal port
docker run -d \
    --name "$CONTAINER_NAME" \
    --network mcp-net \
    -p $PORT:$INTERNAL_PORT \
    -e MCP_HOST="$HOST" \
    -e MCP_PORT="$INTERNAL_PORT" \
    "$IMAGE_NAME"

# Check if the run command was successful
if [ $? -ne 0 ]; then
    echo ""
    echo "Failed to run container. Please check the error messages above."
    exit 1
else
    echo ""
    echo "Container '$CONTAINER_NAME' started successfully in daemon mode."
    echo "You can check its logs with: docker logs $CONTAINER_NAME"
    echo "You can stop it with: docker stop $CONTAINER_NAME"
    echo ""
    echo "The MCP server can be accessed at: http://$HOST:$PORT/sse" on Docker host
    echo "or .. "
    echo "http://$CONTAINER_NAME:$INTERNAL_PORT/sse" from any container on the same Docker [mcp-net] network"
fi