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
if $force_rebuild || ! docker images -q rust-test:latest > /dev/null; then
  echo "Building rust-test:latest image..."
  docker build -t rust-test:latest .
  if [ $? -ne 0 ]; then
    echo "Failed to build rust-test:latest image."
    exit 1
  fi
else
  echo "rust-test:latest image found locally."
fi

# Remote vscode session as user mcp-dev in group mcp-dev needs local directory owned by rust dev and rwx for group
# so, on your dev machine as your user, run the following commands
# There is nothing special about Id 1679
# sudo groupadd -g 1679 mcp-dev
# sudo usermod -aG mcp-dev <user>
# sudo chown -R :mcp-dev /home/parris3142/devroot/mcp
# sudo chmod -R g+rw /home/parris3142/devroot/mcp

# Run the docker command with --rm and volume mount
docker run --rm --name mcp-dev -d -v "$(pwd)/..":/home/mcp-dev/devroot/mcp --user 1679:1679 rust-test:latest tail -f /dev/null