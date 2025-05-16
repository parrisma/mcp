#!/bin/bash

force_rebuild=false

# Parse command-line flags
while getopts "f" opt; do
  case $opt in
    f)
      force_rebuild=true
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      exit 1
      ;;
  esac
done

# Check if the container is running
if docker ps --filter "name=mcp-dev" --format "{{.ID}}" | grep -q .; then
  # Container is running, stop it
  echo "Stopping mcp-dev container..."
  docker stop mcp-dev

  # Remove the container
  echo "Removing mcp-dev container..."
  docker rm mcp-dev
  sleep 15
  echo "Removed mcp-dev container..."
else
  echo "mcp-dev container is not running."
fi

# Check if the image exists locally
if $force_rebuild || ! docker images -q mcp-test:latest > /dev/null; then
  echo "Building mcp-test:latest image..."
  docker build -t mcp-test:latest .
  if [ $? -ne 0 ]; then
    echo "Failed to build mcp-test:latest image."
    exit 1
  fi
else
  echo "mcp-test:latest image found locally."
fi

# Remote vscode session as user mcp-dev in group mcp-dev needs local directory owned by mcp dev and rwx for group
# so, on your dev machine as your user, run the following commands
# There is nothing special about Id 1679
# sudo groupadd -g 1679 mcp-dev
# sudo usermod -aG mcp-dev <user>
# sudo chown -R :mcp-dev /home/parris3142/devroot/mcp
# sudo chmod -R g+rw /home/parris3142/devroot/mcp

# Run the docker command with --rm and volume mount
# Get the GID of the docker group on the host
HOST_DOCKER_GID=$(getent group docker | cut -d: -f3)

# Check if mcp-net network exists, create it if it doesn't
if ! docker network ls | grep -q mcp-net; then
  echo "Creating mcp-net network..."
  docker network create mcp-net
  if [ $? -ne 0 ]; then
    echo "Failed to create mcp-net network."
    exit 1
  fi
  echo "Created mcp-net network."
else
  echo "mcp-net network already exists."
fi

# Run the container with the mcp-dev user (1679) but with the host's docker group.
docker run --rm --name mcp-dev -d \
  -v "$(pwd)/../..":/home/mcp-dev/devroot/mcp \
  -v /var/run/docker.sock:/var/run/docker.sock \
  --network=mcp-net \
  --user 1679:${HOST_DOCKER_GID} \
  mcp-test:latest tail -f /dev/null
