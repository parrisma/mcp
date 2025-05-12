# Use Ubuntu 22.04 LTS as the base image
FROM ubuntu:jammy

# Add metadata labels
LABEL maintainer="MCP Development Team"
LABEL description="Development environment for MCP project"
LABEL version="1.0"

# Set /bin/bash as the default shell
SHELL ["/bin/bash", "-c"]

# Update package lists and install necessary dependencies
RUN apt-get update --fix-missing && \
    apt-get upgrade -y && \
    apt-get install -y \
    curl \
    build-essential \
    pkg-config \
    libudev-dev \
    llvm \
    libclang-dev \
    protobuf-compiler \
    libssl-dev \
    git \
    vim \
    bc \
    jq \
    btop \
    python3-pip && \
    # Purge unnecessary packages
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Miniconda
RUN curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh && \
    bash Miniconda3-latest-Linux-x86_64.sh -b -p /opt/conda && \
    rm Miniconda3-latest-Linux-x86_64.sh

# Add conda to path for all users
ENV PATH="/opt/conda/bin:${PATH}"

# Create conda environment with Python 3.12
RUN conda create -y -n mcp python=3.12 && \
    conda clean -a -y

# Install MCP Python SDK in the conda environment using pip (with CLI extras)
RUN conda run -n mcp pip install "mcp[cli]"

# Create mcp-dev user
RUN groupadd -g 1679 mcp-dev && \
    useradd -u 1679 -g 1679 -m -d /home/mcp-dev -s /bin/bash mcp-dev

USER mcp-dev
ENV HOME=/home/mcp-dev

# Install Node Version Manager (NVM)
RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.4/install.sh | bash

# Export NVM directory to PATH using $HOME
ENV NVM_DIR=$HOME/.nvm
ENV PATH=$NVM_DIR:$NVM_DIR/bin:$PATH
RUN bash -c "source $NVM_DIR/nvm.sh && nvm --version"

# Install Node.js using NVM (specify a Node.js version as needed)
RUN bash -c "source $NVM_DIR/nvm.sh && nvm install --lts && nvm use --lts"
RUN bash -c "source $NVM_DIR/nvm.sh && node -v && npm -v"

# Install Yarn
RUN bash -c "source $NVM_DIR/nvm.sh && npm install --global yarn"
RUN bash -c "source $NVM_DIR/nvm.sh && yarn --version"

# Export conda environment to YAML file
RUN conda env export -n mcp > /home/mcp-dev/mcp_environment.yml && \
    echo "Conda environment exported to /opt/mcp_environment.yml"

# Configure conda for mcp-dev user and set up auto-activation of mcp environment
RUN conda init bash && \
    echo 'conda activate mcp' >> ~/.bashrc

# Set the working directory to the mcp-dev home directory
WORKDIR /home/mcp-dev
