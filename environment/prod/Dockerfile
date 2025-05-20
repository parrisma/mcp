# Use Python 3.12 slim as the base image for a minimal production environment
FROM python:3.12-slim

# Add metadata labels
LABEL maintainer="MCP Development Team"
LABEL description="Production environment for MCP Python server"
LABEL version="1.0"

# Define build argument for the MCP server script path
# This should be the path relative to the Docker build context
ARG MCP_SERVER_SCRIPT="./mcp-server.py"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=6277

# Create a non-root user to run the application
RUN groupadd -g 1000 mcp && \
    useradd -u 1000 -g mcp -s /bin/bash -m mcp

# Install the MCP Python package and dependencies
RUN pip install --no-cache-dir "mcp[cli]"
RUN pip install --no-cache-dir langchain

# Set up the application directory
WORKDIR /app

# Validate the script path is not empty and create a directory for the script
RUN if [ -z "${MCP_SERVER_SCRIPT}" ]; then \
    echo "ERROR: MCP_SERVER_SCRIPT cannot be empty" && exit 1; \
    fi && \
    echo "Using MCP server script: ${MCP_SERVER_SCRIPT}" && \
    mkdir -p /app

# Copy the MCP server script
# The COPY instruction will fail if the file doesn't exist in the build context
COPY --chown=mcp:mcp ${MCP_SERVER_SCRIPT} /app/

# Extract the script filename and make it executable
RUN MCP_SCRIPT_FILENAME=$(basename ${MCP_SERVER_SCRIPT}) && \
    echo "Script filename: ${MCP_SCRIPT_FILENAME}" && \
    chmod +x /app/${MCP_SCRIPT_FILENAME} && \
    echo "export MCP_SCRIPT_FILENAME=${MCP_SCRIPT_FILENAME}" > /app/script_env.sh

# Switch to the non-root user
USER mcp

# Expose the default MCP server port
EXPOSE 6277

# Set the entrypoint to run the MCP server and then keep the container alive
# Using 0.0.0.0 to allow external connections
# Using . instead of source for POSIX shell compatibility
ENTRYPOINT ["sh", "-c", ". /app/script_env.sh && python /app/${MCP_SCRIPT_FILENAME} --host 0.0.0.0 --port 6277 & echo 'MCP server started in background, entering infinite loop'; while true; do sleep 60 & wait $!; done"]

# Default command can be overridden at runtime
CMD []
