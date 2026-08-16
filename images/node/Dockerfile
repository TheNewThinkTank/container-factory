FROM node:26.7-trixie-slim

LABEL \
    org.opencontainers.image.title="Node.js" \
    org.opencontainers.image.description="Node.js 26.7 runtime based on Debian Trixie slim; npm omitted from the runtime image" \
    org.opencontainers.image.source="https://github.com/TheNewThinkTank/container-factory"

# Install the latest available Debian security updates.
RUN apt-get update \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/*

# This is a runtime image, not a Node.js build image. Remove the bundled npm
# toolchain so its transitive dependencies do not become runtime attack surface.
# Applications should install dependencies during a separate build stage.
RUN rm -rf /usr/local/lib/node_modules/npm \
    && rm -f /usr/local/bin/npm /usr/local/bin/npx

WORKDIR /workspace

# The official Node image provides the unprivileged `node` user.
USER node

CMD ["node", "--version"]
