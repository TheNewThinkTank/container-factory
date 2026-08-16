FROM nginx:1.30.4-alpine3.24

LABEL \
    org.opencontainers.image.title="Nginx" \
    org.opencontainers.image.description="Nginx 1.30.4 web server based on Alpine Linux 3.24" \
    org.opencontainers.image.source="https://github.com/TheNewThinkTank/container-factory"

# Run Nginx without root privileges.
RUN sed -i 's/listen       80;/listen       8080;/' /etc/nginx/conf.d/default.conf \
    && sed -i 's/listen \[::\]:80;/listen [::]:8080;/' /etc/nginx/conf.d/default.conf \
    && mkdir -p /var/cache/nginx /var/run/nginx \
    && chown -R nginx:nginx /var/cache/nginx /var/run/nginx /etc/nginx/conf.d

USER nginx

EXPOSE 8080

CMD ["nginx", "-g", "daemon off; pid /tmp/nginx.pid;"]
