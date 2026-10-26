# ProcureLens web UI (Next.js 15). Built by `docker compose up api web` from the repo root.
# The browser calls the API directly, so its address is baked in at build time (NEXT_PUBLIC_*).
FROM node:22-alpine AS build
WORKDIR /web
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM node:22-alpine
WORKDIR /web
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1
COPY --from=build /web/package.json /web/package-lock.json ./
COPY --from=build /web/node_modules ./node_modules
COPY --from=build /web/.next ./.next
COPY --from=build /web/public ./public
EXPOSE 3100
CMD ["npx", "next", "start", "-p", "3100", "-H", "0.0.0.0"]
