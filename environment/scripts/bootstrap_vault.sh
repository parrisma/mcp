#!/bin/bash

# Default values
VAULT_HOST="0.0.0.0"
VAULT_PORT="8200"
FORCE=false

# Parse command line arguments
while getopts "h:p:f" opt; do
    case $opt in
        h) VAULT_HOST="$OPTARG" ;;
        p) VAULT_PORT="$OPTARG" ;;
        f) FORCE=true ;;
        \?) echo "Invalid option -$OPTARG" >&2; exit 1 ;;
    esac
done

# Check if container is already running and force flag is set
if [ "$FORCE" = true ]; then
    if docker ps -a --format '{{.Names}}' | grep -q "^vault-dev$"; then
        echo "Stopping existing vault-dev container..."
        docker stop vault-dev >/dev/null 2>&1
        docker rm vault-dev >/dev/null 2>&1
    fi
fi
# Check if vault-dev container is already running
if docker ps --format '{{.Names}}' | grep -q "^vault-dev$"; then
    echo "Vault container is already running."
    exit 0
fi

# Check if container exists but is not running
if docker ps -a --format '{{.Names}}' | grep -q "^vault-dev$"; then
    echo "Found stopped vault-dev container. Starting it..."
    docker start vault-dev
    echo "Vault server started on ${VAULT_HOST}:${VAULT_PORT}"
    exit 0
fi

# If we get here, no vault-dev container exists
echo "Creating new vault-dev container..."
# Run vault container
docker run -d --name vault-dev \
--network mcp-net \
-p ${VAULT_PORT}:8200 \
-e 'VAULT_DEV_ROOT_TOKEN_ID=devroot' \
-e "VAULT_DEV_LISTEN_ADDRESS=${VAULT_HOST}:8200" \
hashicorp/vault:latest

echo "Vault server started on ${VAULT_HOST}:${VAULT_PORT}"