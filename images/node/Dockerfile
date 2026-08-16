FROM node:26.7-trixie-slim

LABEL \
    org.opencontainers.image.title="Node.js" \
    org.opencontainers.image.description="Node.js 26.7 runtime based on Debian Trixie slim" \
    org.opencontainers.image.source="https://github.com/TheNewThinkTank/container-factory"

# Install the latest available Debian security updates.
RUN apt-get update \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/*

# Update npm to a release whose bundled dependency tree contains the patched
# brace-expansion and ip-address versions required by the security policy.
RUN npm install --global npm@12.0.1 \
    && npm cache clean --force

WORKDIR /workspace

# The official Node image provides the unprivileged `node` user.
USER node

CMD ["node", "--version"]
