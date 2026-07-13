FROM node:22-bookworm-slim

ENV NEXT_TELEMETRY_DISABLED=1

WORKDIR /app

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build \
    && npm prune --omit=dev

EXPOSE 3000

CMD ["npm", "run", "start", "--", "-H", "0.0.0.0"]
