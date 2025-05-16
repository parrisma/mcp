#!/bin/bash

# Get the home directory of the current user
HOME_DIR="$HOME"

# Default values
IMAGE_NAME="mcp-prod"
DEVROOT_DIR="devroot"
MCP_SERVER_SCRIPT="mcp/python/src/mcp-server.py"
DOCKERFILE="$HOME_DIR/$DEVROOT_DIR/mcp/environment/prod/Dockerfile"
BUILD_CONTEXT="$HOME_DIR/$DEVROOT_DIR"
HOST="0.0.0.0"
PORT="6277"  # External port that will be mapped to the container
INTERNAL_PORT="6277"  # Internal container port where the MCP server listens
CONTAINER_NAME="mcp-prd-svc"

# Display usage information
function show_usage {
    echo "Usage: $0 [OPTIONS]"
    echo "Build the MCP production container with configurable options."
    echo ""
    echo "Options:"
    echo "  -i, --image NAME       Set the image name/tag (default: $IMAGE_NAME)"
    echo "  -d, --devroot DIR      Set the devroot directory name (default: $DEVROOT_DIR)"
    echo "  -s, --script PATH      Set the MCP server script path (default: $MCP_SERVER_SCRIPT)"
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
        -d|--devroot)
            DEVROOT_DIR="$2"
            # Update paths that depend on DEVROOT_DIR
            DOCKERFILE="$HOME_DIR/$DEVROOT_DIR/mcp/environment/prod/Dockerfile"
            BUILD_CONTEXT="$HOME_DIR/$DEVROOT_DIR"
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
echo "  Devroot dir:   $DEVROOT_DIR"
echo "  Server script: $MCP_SERVER_SCRIPT"
echo "  Dockerfile:    $DOCKERFILE"
echo "  Build context: $BUILD_CONTEXT"
echo ""

# Build the Docker image
docker build -t "$IMAGE_NAME" \
    --build-arg "MCP_SERVER_SCRIPT=$MCP_SERVER_SCRIPT" \
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