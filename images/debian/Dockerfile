FROM debian:trixie-slim

LABEL \
    org.opencontainers.image.title="Debian" \
    org.opencontainers.image.description="Debian 13 (Trixie) slim base image with current security updates" \
    org.opencontainers.image.source="https://github.com/TheNewThinkTank/container-factory"

# Install the latest available Debian security updates.
RUN apt-get update \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

RUN useradd \
        --create-home \
        --uid 10001 \
        --shell /usr/sbin/nologin \
        appuser \
    && chown appuser:appuser /workspace

USER appuser

CMD ["sh", "-c", "cat /etc/debian_version"]
