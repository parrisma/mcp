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
    python3-pip \
    ca-certificates \
    gnupg \
    wget \
    iputils-ping \
    lsb-release && \
    # Purge unnecessary packages.
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Docker
ARG DOCKER_GID=1001
RUN groupadd -g ${DOCKER_GID} docker
RUN mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null && \
    apt-get update && \
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Miniconda
RUN curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh && \
    bash Miniconda3-latest-Linux-x86_64.sh -b -p /opt/conda && \
    rm Miniconda3-latest-Linux-x86_64.sh

# Add conda to path for all users
ENV PATH="/opt/conda/bin:${PATH}"

# Create mcp-dev user and add to docker group
ARG MCP_DEV_GID=1679
ARG MCP_DEV_UID=1679
RUN groupadd -g ${MCP_DEV_GID} mcp-dev
RUN useradd -u ${MCP_DEV_UID} -g ${MCP_DEV_GID} -m -d /home/mcp-dev -s /bin/bash mcp-dev
RUN usermod -aG docker mcp-dev    

USER mcp-dev
RUN echo 'umask 0006' >> ~/.bashrc
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

# Configure conda for mcp-dev user and set up auto-activation of mcp environment
RUN conda init bash

# Create conda environment with Python 3.12
RUN conda create -y -n mcp python=3.12
RUN conda clean -a -y

# Install MCP Python SDK in the conda environment using pip (with CLI extras)
RUN conda run -n mcp pip install mcp-server
RUN conda run -n mcp pip install "mcp[cli]"
RUN conda run -n mcp pip install docker
RUN conda run -n mcp pip install pytest
RUN conda run -n mcp conda install -c conda-forge langchain
RUN conda run -n mcp conda install -c conda-forge ollama
RUN conda run -n mcp conda install -c conda-forge ollama-python
RUN conda run -n mcp conda install anaconda::flask
RUN conda run -n mcp conda install -c conda-forge flask-cors
RUN conda run -n mcp pip install chromadb


RUN conda clean -a -y
RUN echo 'conda activate mcp' >> ~/.bashrc

# Export conda environment to YAML file
RUN conda env export -n mcp > /home/mcp-dev/mcp_environment.yml && \
    echo "Conda environment exported to /opt/mcp_environment.yml"

# --- React App Setup: Install Dependencies Only ---
WORKDIR /home/mcp-dev/react/mcp-app

COPY --chown=mcp-dev:mcp-dev react/mcp-app/package.json ./package.json
# DONT copy ./package-lock.json as we want to force a fresh install

RUN curl -I https://registry.npmjs.org

ENV NVM_DIR=/home/mcp-dev/.nvm
ENV NODE_VERSION=20.17.0

RUN bash -c "curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.1/install.sh | bash && \
    source $NVM_DIR/nvm.sh && \
    nvm install $NODE_VERSION && \
    nvm alias default $NODE_VERSION && \
    nvm use $NODE_VERSION && \
    npm install -g npm@latest"

# --- End React App Setup ---

# Set the working directory to the mcp-dev home directory
WORKDIR /home/mcp-dev

# Copy the entrypoint script
COPY environment/dev/docker-entrypoint.sh /usr/local/bin/
USER root
RUN chmod +x /usr/local/bin/docker-entrypoint.sh
USER mcp-dev

# Set the entrypoint
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["bash"]
