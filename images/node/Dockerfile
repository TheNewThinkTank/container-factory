FROM node:24.18.0-bookworm-slim

LABEL \
    org.opencontainers.image.title="Node.js" \
    org.opencontainers.image.description="Node.js 24.18.0 runtime based on Debian Bookworm slim" \
    org.opencontainers.image.source="https://github.com/TheNewThinkTank/container-factory"

# Install the latest available Debian security updates.
RUN apt-get update \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# The official Node image provides the unprivileged `node` user.
USER node

CMD ["node", "--version"]
