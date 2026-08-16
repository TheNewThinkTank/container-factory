FROM ubuntu:24.04

LABEL \
    org.opencontainers.image.title="Ubuntu" \
    org.opencontainers.image.description="Ubuntu 24.04 LTS base image with current security updates" \
    org.opencontainers.image.source="https://github.com/TheNewThinkTank/container-factory"

# Install the latest available Ubuntu security updates.
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

RUN useradd \
        --create-home \
        --uid 10001 \
        --shell /usr/sbin/nologin \
        appuser \
    && chown appuser:appuser /workspace

USER appuser

CMD ["sh", "-c", "cat /etc/os-release"]
