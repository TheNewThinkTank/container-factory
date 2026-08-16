FROM node:26.7-trixie-slim

LABEL \
    org.opencontainers.image.title="Node.js" \
    org.opencontainers.image.description="Node.js 26.7 runtime based on Debian Trixie slim" \
    org.opencontainers.image.source="https://github.com/TheNewThinkTank/container-factory"

# Install the latest available Debian security updates.
RUN apt-get update \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# The official Node image provides the unprivileged `node` user.
USER node

CMD ["node", "--version"]
