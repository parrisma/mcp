#!/bin/bash

DEBUG=1 # Set to 1 to enable debug mode

RUN_IN_DEV_CONTAINER=1 # Set to 1 to run in a dev container

HOME_DIR="$HOME" # Get the home directory of the current user
MCP_ROOT_DIR="mcp" # Project folder under build context
if [ "$RUN_IN_DEV_CONTAINER" = "1" ]; then
    BUILD_CONTEXT="/$MCP_ROOT_DIR" # Inside the dev container, the build context is the root of the project
else
    BUILD_CONTEXT="$HOME_DIR/devroot/$MCP_ROOT_DIR" # Realtive to user home directory
fi
MCP_SERVER_SCRIPT="./python/src/mcp-server.py" # Path to the MCP server script relative to the build context
MCP_SERVER_CONFIG="./config/mcp-server-config.json" # Path to the MCP server script relative to the build context
DOCKERFILE="$BUILD_CONTEXT/environment/prod/Dockerfile" # Absolute path to the Dockerfile

CONTAINER_NAME="mcp-prd-svc"
IMAGE_NAME="mcp-prod"

HOST="0.0.0.0"
PORT="6277"  # External port that will be mapped to the container
INTERNAL_PORT="6277"  # Internal container port where the MCP server listens

# Display usage information
function show_usage {
    echo "Usage: $0 [OPTIONS]"
    echo "Build the MCP production container with configurable options."
    echo ""
    echo "Options:"
    echo "  -i, --image NAME       Set the image name/tag (default: $IMAGE_NAME)"
    echo "  -d, --mcproot DIR      Set the mcp root directory name (default: $MCP_ROOT_DIR)"
    echo "  -s, --script PATH      Set the MCP server script path (default: $MCP_SERVER_SCRIPT)"
    echo "  --config PATH          Set the MCP server config path (default: $MCP_SERVER_CONFIG)"
    echo "  -f, --dockerfile PATH  Set the Dockerfile path (default: $DOCKERFILE)"
    echo "  -c, --context PATH     Set the build context path (default: $BUILD_CONTEXT)"
    echo "  --host HOST            Set the host to bind to (default: $HOST)"
    echo "  -p, --port PORT        Set the external port to bind to (default: $PORT)"
    echo "  -n, --name NAME        Set the container name (default: $CONTAINER_NAME)"
    echo "  -h, --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --image custom-mcp --script custom/path/to/script.py"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -i|--image)
            IMAGE_NAME="$2"
            shift 2
        ;;
        -d|--mcproot)
            MCP_ROOT_DIR="$2"
            # Update paths that depend on DEVROOT_DIR
            MCP_SERVER_SCRIPT="$MCP_ROOT_DIR/python/src/mcp-server.py"
            MCP_SERVER_CONFIG="$MCP_ROOT_DIR/python/src/mcp-server-config.json"
            DOCKERFILE="$MCP_ROOT_DIR/environment/prod/Dockerfile"
            BUILD_CONTEXT="$MCP_ROOT_DIR"
            shift 2
        ;;
        -s|--script)
            MCP_SERVER_SCRIPT="$2"
            shift 2
        ;;
        -f|--dockerfile)
            DOCKERFILE="$2"
            shift 2
        ;;
        -c|--context)
            BUILD_CONTEXT="$2"
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
        -n|--name)
            CONTAINER_NAME="$2"
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

# Display configuration
echo "Building MCP production container with the following configuration:"
echo "  Image name:    $IMAGE_NAME"
echo "  MCP root dir:  $MCP_ROOT_DIR"
echo "  Server script: $MCP_SERVER_SCRIPT"
echo "  Server Config: $MCP_SERVER_CONFIG"
echo "  Dockerfile:    $DOCKERFILE"
echo "  Build context: $BUILD_CONTEXT"
echo ""

# Build the Docker image
if [ "$DEBUG" = "1" ]; then
    echo "docker build -t \"$IMAGE_NAME\" --build-arg \"MCP_SERVER_SCRIPT=$MCP_SERVER_SCRIPT\" --build-arg \"MCP_SERVER_CONFIG=$MCP_SERVER_CONFIG\" -f \"$DOCKERFILE\" \"$BUILD_CONTEXT\""
fi

docker build -t "$IMAGE_NAME" \
--build-arg "MCP_SERVER_SCRIPT=$MCP_SERVER_SCRIPT" \
--build-arg "MCP_SERVER_CONFIG=$MCP_SERVER_CONFIG" \
-f "$DOCKERFILE" \
"$BUILD_CONTEXT"

# Check if the build was successful
if [ $? -ne 0 ]; then
    echo ""
    echo "Build failed. Please check the error messages above."
    exit 1
fi

echo ""
echo "Build successful! The image '$IMAGE_NAME' is now available."

# Show how to run the container
echo "You can run it with the run-prod-container.sh script:"
echo "  ./run-prod-container.sh --image $IMAGE_NAME"

exit 0