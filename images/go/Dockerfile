FROM golang:1.26.5-bookworm

LABEL \
    org.opencontainers.image.title="Go" \
    org.opencontainers.image.description="Go 1.26.5 development runtime based on Debian Bookworm" \
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

CMD ["go", "version"]
