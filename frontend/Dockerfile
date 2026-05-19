FROM node:20-alpine AS builder

WORKDIR /app

ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

# Render sets NODE_ENV=production; devDependencies are required for next build
COPY package*.json ./
RUN npm install --include=dev

COPY . .

# Avoid OOM on Render free tier during build
ENV NODE_OPTIONS=--max-old-space-size=512
RUN npm run build

# --- Production image ---
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production

ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

COPY package*.json ./
RUN npm install --omit=dev

COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/next.config.ts ./next.config.ts

# Render sets PORT (usually 10000)
CMD ["sh", "-c", "npm run start -- -H 0.0.0.0 -p ${PORT:-3000}"]
