FROM alpine:3.24

LABEL org.opencontainers.image.title="container-factory hello" \
      org.opencontainers.image.description="Tiny smoke-test image for container-factory" \
      org.opencontainers.image.source="https://github.com/TheNewThinkTank/container-factory"

WORKDIR /workspace

RUN adduser \
    -D \
    -H \
    -u 10001 \
    -s /sbin/nologin \
    appuser \
    && chown appuser:appuser /workspace

USER appuser

CMD ["sh", "-c", "echo 'container-factory: hello'"]
