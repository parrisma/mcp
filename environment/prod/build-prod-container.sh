#!/bin/bash

DEBUG=1 # Set to 1 to enable debug mode

RUN_IN_DEV_CONTAINER=1 # Set to 1 to run in a dev container

HOME_DIR="$HOME" # Get the home directory of the current user
MCP_ROOT_DIR="mcp" # Project folder under build context
# BUILD_CONTEXT and DOCKERFILE will be set after parsing arguments,
# as they depend on RUN_IN_DEV_CONTAINER and MCP_ROOT_DIR.
MCP_SERVER_SCRIPT="mcp_server_runner.py" # Filename of the MCP server script
MCP_SERVER_CONFIG="./config/mcp-server-config.json" # Path to the MCP server config relative to the build context
MCP_SCRIPTS_DIR="./python/src/server/" # Path to the directory containing MCP scripts, relative to the build context
# DOCKERFILE will be set later

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
    echo "  -i, --image NAME         Set the image name/tag (default: $IMAGE_NAME)"
    echo "  -d, --mcproot DIR        Set the mcp root directory name (default: $MCP_ROOT_DIR)"
    echo "  -s, --script FILENAME    Set the MCP server script filename (default: $MCP_SERVER_SCRIPT)"
    echo "    , --config PATH        Set the MCP server config path (default: $MCP_SERVER_CONFIG)"
    echo "    , --scripts-src PATH   Set the source directory for MCP scripts (build arg MCP_SCRIPTS_DIR, default: $MCP_SCRIPTS_DIR)"
    echo "    , --dev-container-mode <0|1> Set whether running in dev container mode (affects build context, default: $RUN_IN_DEV_CONTAINER)"
    echo "  -f, --dockerfile PATH    Set the Dockerfile path (will be derived if not set)"
    echo "  -c, --context PATH       Set the build context path (will be derived if not set)"
    echo "    , --host HOST          Set the host to bind to (default: $HOST)"
    echo "  -p, --port PORT          Set the external port to bind to (default: $PORT)"
    echo "  -n, --name NAME          Set the container name (default: $CONTAINER_NAME)"
    echo "  -h, --help               Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --image custom-mcp --script my_runner.py --scripts-src ./custom_scripts_dir/"
}
9135154
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
            # Update BUILD_CONTEXT and DOCKERFILE based on new MCP_ROOT_DIR
            if [ "$RUN_IN_DEV_CONTAINER" = "1" ]; then
                BUILD_CONTEXT="/$MCP_ROOT_DIR"
            else
                BUILD_CONTEXT="$HOME_DIR/devroot/$MCP_ROOT_DIR"
            fi
            DOCKERFILE="$BUILD_CONTEXT/environment/prod/Dockerfile"
            # MCP_SERVER_SCRIPT (filename), MCP_SERVER_CONFIG (relative path), and MCP_SCRIPTS_DIR (relative path)
            # are not changed here as they are relative to the BUILD_CONTEXT or just a filename.
            shift 2
        ;;
        --config)
            MCP_SERVER_CONFIG="$2"
            shift 2
        ;;
        --scripts-src)
            MCP_SCRIPTS_DIR="$2"
            shift 2
        ;;
        --dev-container-mode)
            if [[ "$2" == "0" || "$2" == "1" ]]; then
                RUN_IN_DEV_CONTAINER="$2"
            else
                echo "Error: --dev-container-mode must be 0 or 1." >&2
                show_usage
                exit 1
            fi
            shift 2
        ;;
        -s|--script)
            MCP_SERVER_SCRIPT="$2"
            shift 2
        ;;
        -f|--dockerfile)
            DOCKERFILE_OVERRIDE="$2" # Store override, apply after all args parsed
            shift 2
        ;;
        -c|--context)
            BUILD_CONTEXT_OVERRIDE="$2" # Store override, apply after all args parsed
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

# Now that all arguments are parsed, determine BUILD_CONTEXT and DOCKERFILE
if [ "$RUN_IN_DEV_CONTAINER" = "1" ]; then
    # If BUILD_CONTEXT was not explicitly set by -c/--context, derive it
    if [ -z "$BUILD_CONTEXT_OVERRIDE" ]; then
      BUILD_CONTEXT="/$MCP_ROOT_DIR" # Inside the dev container
    fi
else
    # If BUILD_CONTEXT was not explicitly set by -c/--context, derive it
    if [ -z "$BUILD_CONTEXT_OVERRIDE" ]; then
      BUILD_CONTEXT="$HOME_DIR/devroot/$MCP_ROOT_DIR" # Relative to user home directory
    fi
fi
# If DOCKERFILE was not explicitly set by -f/--dockerfile, derive it
if [ -z "$DOCKERFILE_OVERRIDE" ]; then
  DOCKERFILE="$BUILD_CONTEXT/environment/prod/Dockerfile"
fi
# Use overridden values if they were set
BUILD_CONTEXT="${BUILD_CONTEXT_OVERRIDE:-$BUILD_CONTEXT}"
DOCKERFILE="${DOCKERFILE_OVERRIDE:-$DOCKERFILE}"

# Validate that the derived MCP server script exists on the host
if [ ! -f "$BUILD_CONTEXT/$MCP_SCRIPTS_DIR/$MCP_SERVER_SCRIPT" ]; then
    echo "Error: MCP Server Script not found at '$BUILD_CONTEXT/$MCP_SCRIPTS_DIR/$MCP_SERVER_SCRIPT'" >&2
    echo "This path was derived from  :" >&2
    echo "  Build Context             : $BUILD_CONTEXT" >&2
    echo "  MCP Scripts Directory     : $MCP_SCRIPTS_DIR" >&2
    echo "  MCP Server Script Filename: $MCP_SERVER_SCRIPT" >&2
    exit 1
fi

# Display configuration
echo "Building MCP production container with the following configuration:"
echo "  Image name:    $IMAGE_NAME"
echo "  Run in dev container mode: $RUN_IN_DEV_CONTAINER"
echo "  MCP root dir:  $MCP_ROOT_DIR"
echo "  Build Context: $BUILD_CONTEXT"
echo "  Server script filename: $MCP_SERVER_SCRIPT"
echo "  Server script directory (relative to context): $MCP_SCRIPTS_DIR"
echo "  Server Config (relative to context): $MCP_SERVER_CONFIG"
echo "  Scripts Source for Docker ARG (MCP_SCRIPTS_DIR, relative to context): $MCP_SCRIPTS_DIR"
echo "  Dockerfile:    $DOCKERFILE"
echo ""

# Build the Docker image
if [ "$DEBUG" = "1" ]; then
    echo "docker build -t \"$IMAGE_NAME\" --build-arg \"MCP_SERVER_SCRIPT=$MCP_SERVER_SCRIPT\" --build-arg \"MCP_SERVER_CONFIG=$MCP_SERVER_CONFIG\" --build-arg \"MCP_SCRIPTS_DIR=$MCP_SCRIPTS_DIR\" -f \"$DOCKERFILE\" \"$BUILD_CONTEXT\""
fi

docker build -t "$IMAGE_NAME" \
--build-arg "MCP_SERVER_SCRIPT=$MCP_SERVER_SCRIPT" \
--build-arg "MCP_SERVER_CONFIG=$MCP_SERVER_CONFIG" \
--build-arg "MCP_SCRIPTS_DIR=$MCP_SCRIPTS_DIR" \
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