FROM ubuntu:latest

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        python3-venv \
        git \
        wget \
        ca-certificates \
        gnupg \
        build-essential \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Install git-lfs
RUN curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | bash && \
    apt-get update && apt-get install -y git-lfs && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Copy entrypoint into image
COPY scripts/container_entrypoint.sh /usr/local/bin/container_entrypoint.sh
RUN chmod +x /usr/local/bin/container_entrypoint.sh

ENTRYPOINT ["/usr/local/bin/container_entrypoint.sh"]
