#!/bin/bash
set -e

# Check if Docker socket is mounted from host
if [ -S /var/run/docker.sock ]; then
  echo "Using host Docker daemon via mounted socket..."
  
  # Fix Docker socket permissions if running as non-root
  if [ "$(id -u)" != "0" ]; then
    # Check if we can access the socket
    if ! docker ps >/dev/null 2>&1; then
      echo "Fixing Docker socket permissions..."
      # We need to run this with sudo, which requires the container to be started with --privileged
      if command -v sudo >/dev/null 2>&1; then
        sudo chmod 666 /var/run/docker.sock
      else
        echo "Warning: Cannot fix Docker socket permissions. Container needs to be run with correct GID or as privileged."
      fi
    fi
  fi
else
  # Start Docker daemon if it's not running and socket is not mounted
  if ! pgrep -f dockerd >/dev/null; then
    echo "Starting Docker daemon..."
    dockerd &
    # Wait for Docker daemon to start
    sleep 3
  fi
fi

# Execute the command passed to the script
exec "$@"