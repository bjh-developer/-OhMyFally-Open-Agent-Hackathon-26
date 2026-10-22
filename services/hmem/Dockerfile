# Build context is ./services (see docker-compose.yml) so the official conformance suite is available.
FROM node:22-alpine
WORKDIR /app/hmem

COPY hmem/package.json hmem/package-lock.json ./
RUN npm ci --omit=dev

COPY hmem/src ./src
COPY hmem-upstream/conformance /app/hmem-upstream/conformance

# Building the image runs the official H-MEM conformance suite; a failure fails the build,
# and GET /healthz reports "pass" only because this file exists.
RUN HMEM_IMPL=/app/hmem/src/index.ts node --import tsx /app/hmem-upstream/conformance/runner.ts \
    && echo pass > conformance.status

ENV PORT=7070 \
    HMEM_STATE_DIR=/data/state \
    HMEM_LEDGER_LOG=/data/logs/hmem-ledger.jsonl \
    HMEM_CONFORMANCE_FILE=/app/hmem/conformance.status
VOLUME ["/data/state"]
EXPOSE 7070
HEALTHCHECK --interval=5s --timeout=3s --retries=10 CMD wget -q -O /dev/null http://127.0.0.1:7070/healthz || exit 1
CMD ["node", "--import", "tsx", "src/server.ts"]
