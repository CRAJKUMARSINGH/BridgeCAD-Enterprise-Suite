# ─────────────────────────────────────────────────────────────────────────────
# BridgeCAD Web Console — multi-arch Dockerfile (React/Vite + nginx)
# Targets: linux/amd64  linux/arm64
# ─────────────────────────────────────────────────────────────────────────────

# ── Stage 1: node build ───────────────────────────────────────────────────
FROM node:20-alpine AS build

WORKDIR /app
COPY apps/web-console/package.json apps/web-console/package-lock.json* ./
RUN npm ci --prefer-offline

COPY apps/web-console/ .

# Inject API URL at build time (overrideable via --build-arg)
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# ── Stage 2: nginx serving ────────────────────────────────────────────────
FROM nginx:1.27-alpine AS runtime

# Remove default nginx config
RUN rm -rf /etc/nginx/conf.d/default.conf

# SPA nginx config — all routes fall back to index.html
RUN printf 'server {\n\
    listen 80;\n\
    root /usr/share/nginx/html;\n\
    index index.html;\n\
    gzip on;\n\
    gzip_types text/css application/javascript application/json image/svg+xml;\n\
    location / {\n\
        try_files $uri $uri/ /index.html;\n\
    }\n\
    location /health {\n\
        return 200 "ok";\n\
        add_header Content-Type text/plain;\n\
    }\n\
}\n' > /etc/nginx/conf.d/bridgecad.conf

COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -qO- http://localhost/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
