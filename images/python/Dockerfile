FROM python:3.14.7-slim-trixie

ENV \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

LABEL \
    org.opencontainers.image.title="Python" \
    org.opencontainers.image.description="Python 3.14.7 runtime based on Debian Trixie slim" \
    org.opencontainers.image.source="https://github.com/TheNewThinkTank/container-factory"

WORKDIR /workspace

# Install the latest available Debian security updates.
RUN apt-get update \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/*

# Run as an unprivileged user.
RUN useradd \
        --create-home \
        --uid 10001 \
        --shell /usr/sbin/nologin \
        appuser

USER appuser

CMD ["python", "--version"]
