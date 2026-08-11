FROM python:3.14-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

LABEL org.opencontainers.image.title="Python" \
      org.opencontainers.image.description="Python 3.13 runtime based on Debian Bookworm slim" \
      org.opencontainers.image.source="https://github.com/TheNewThinkTank/container-factory"

WORKDIR /workspace

CMD ["python", "--version"]
