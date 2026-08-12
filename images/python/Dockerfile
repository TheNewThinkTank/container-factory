FROM python:3.14-slim-trixie

ENV \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

LABEL \
    org.opencontainers.image.title="Python" \
    org.opencontainers.image.description="Python 3.14 runtime based on Debian Trixie slim" \
    org.opencontainers.image.source="https://github.com/TheNewThinkTank/container-factory"

WORKDIR /workspace

RUN \
    apt-get update \
    && apt-get upgrade -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

CMD ["python", "--version"]
