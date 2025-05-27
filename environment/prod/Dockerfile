# Use Python 3.12 slim as the base image for a minimal production environment
FROM python:3.12-slim

# Add metadata labels
LABEL maintainer="MCP Development Team"
LABEL description="Production environment for MCP Python server"
LABEL version="1.0"

# Define build argument for the MCP server script path
# This should be the path relative to the Docker build context
ARG MCP_SERVER_SCRIPT="mcp_server_runner.py" # Path to the main server script, relative to the build context. Assumed to be within MCP_SCRIPTS_DIR.
ARG MCP_SCRIPTS_DIR="./mcp/python/src/server/" # Default path for additional scripts/modules needed by the server
ARG MCP_SERVER_CONFIG="./mcp/python/config/mcp-server-config.json"

RUN pwd
RUN echo "MCP_SERVER_SCRIPT=${MCP_SERVER_SCRIPT}"
RUN echo "MCP_SCRIPTS_DIR=${MCP_SCRIPTS_DIR}"
RUN echo "MCP_SERVER_CONFIG=${MCP_SERVER_CONFIG}"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=6277

    # Update package lists and install necessary dependencies
RUN apt-get update --fix-missing && \
    apt-get upgrade -y && \
    apt-get install -y \
    wget \
    iputils-ping && \
    # Purge unnecessary packages.
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create a non-root user to run the application
RUN groupadd -g 1000 mcp && \
    useradd -u 1000 -g mcp -s /bin/bash -m mcp

# Install the MCP Python package and dependencies
RUN pip install --no-cache-dir "mcp[cli]"
RUN pip install --no-cache-dir langchain

# Set up the application directory
WORKDIR /app

# Copy additional Python scripts/modules from the directory specified by MCP_SCRIPTS_DIR
# These might be dependencies for the MCP_SERVER_SCRIPT.
# Ensure MCP_SCRIPTS_DIR is relative to the Docker build context.
# The contents of this directory (e.g., all files and subdirectories) will be copied into /app/
COPY --chown=mcp:mcp ${MCP_SCRIPTS_DIR}/. /app/

# MCP_SERVER_SCRIPT (defined by ARG) is now expected to be copied as part of MCP_SCRIPTS_DIR.
# Its presence in /app/ and executability are implicitly handled by the subsequent COPY and ENTRYPOINT logic.

# Validate the config path is not empty
RUN if [ -z "${MCP_SERVER_CONFIG}" ]; then \
    echo "ERROR: MCP_SERVER_CONFIG cannot be empty" && exit 1; \
    fi 
COPY --chown=mcp:mcp ${MCP_SERVER_CONFIG} /app/

# Define the server script and config script filenames as environment variables to use in the entrypoint
RUN echo "export MCP_SCRIPT_FILENAME=${MCP_SERVER_SCRIPT}" > /app/script_env.sh && \
    echo "export MCP_CONFIG_FILE=$(basename "${MCP_SERVER_CONFIG}")" >> /app/script_env.sh

# Switch to the non-root user
USER mcp

# Expose the default MCP server port
EXPOSE 6277

# Set the entrypoint to run the MCP server and then keep the container alive
# Using 0.0.0.0 to allow external connections
# Using . instead of source for POSIX shell compatibility
ENTRYPOINT ["bash", "-c", ". /app/script_env.sh && cat /app/script_env.sh && python /app/${MCP_SCRIPT_FILENAME} --host 0.0.0.0 --port 6277 --config-dir . --config-file ${MCP_CONFIG_FILE}; while true; do sleep 60 & wait $!; done"]

# Default command can be overridden at runtime
CMD []
