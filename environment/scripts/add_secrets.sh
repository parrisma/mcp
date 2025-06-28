#!/bin/bash

# Check if the correct number of arguments is provided
if [ "$#" -lt 3 ]; then
    echo "Usage: $0 <secret_name> <key> <value> [host] [port]"
    echo "  host: Vault host (default: vault-dev)"
    echo "  port: Vault port (default: 8200 for https)"
    exit 1
fi

# Assign arguments to variables for clarity
SECRET_NAME=$1
KEY=$2
VALUE=$3

# Set the vault host and port with defaults
VAULT_HOST=${4:-"vault-dev"} # set host to localhost when running outside of mcp-net
VAULT_PORT=${5:-"8200"}

# In dev mode, Vault uses HTTP
PROTOCOL="http"

# Execute vault command to add or update the secret
curl -s -k -X POST -H "Content-Type: application/json" \
-H "X-Vault-Token: devroot" \
-d "{\"data\": {\"${KEY}\": \"${VALUE}\"}}" \
"${PROTOCOL}://${VAULT_HOST}:${VAULT_PORT}/v1/secret/data/${SECRET_NAME}" > /dev/null || {
    echo "Failed to add secret to vault";
    exit 1;
}

# Add a small delay to allow time for the secret to be processed
sleep 1

# Verify that the secret was added correctly
echo "Verifying secret was added..."
RESPONSE=$(curl -s -k -H "X-Vault-Token: devroot" "${PROTOCOL}://${VAULT_HOST}:${VAULT_PORT}/v1/secret/data/${SECRET_NAME}")

# Check if we got a valid response
if [ $? -ne 0 ]; then
    echo "Failed to verify secret"
    exit 1
fi

# Check if the key exists in the response
if ! echo "$RESPONSE" | grep -q "\"${KEY}\""; then
    echo "Secret verification failed: ${KEY} not found in response"
    echo "Response was: $RESPONSE"
    exit 1
fi

# Add a blank line for better output formatting
echo ""
echo "Secret ${KEY} successfully added/updated at ${SECRET_NAME} on ${VAULT_HOST}:${VAULT_PORT}"