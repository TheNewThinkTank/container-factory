# golang:trixie (without -slim) is intentional: this image ships the full Go
# toolchain (compiler, stdlib, go tool) so users can compile and run Go code
# inside the container. The larger footprint is the expected trade-off for a
# development-runtime image.
FROM golang:1.26.6-trixie

LABEL \
    org.opencontainers.image.title="Go" \
    org.opencontainers.image.description="Go 1.26.6 development runtime based on Debian Trixie" \
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
