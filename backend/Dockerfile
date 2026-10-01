FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies needed for native builds
RUN apk add --no-cache openssl libc6-compat

# Copy package descriptors
COPY package*.json ./
COPY prisma ./prisma/

# Install dependencies
RUN npm ci || npm install

# Copy application source and data
COPY . .

# Generate Prisma Client and compile NestJS app
RUN npx prisma generate --schema=prisma/schema.postgresql.prisma
RUN npm run build || npx tsc -p tsconfig.json

# Runner stage
FROM node:20-alpine AS runner

WORKDIR /app

RUN apk add --no-cache openssl libc6-compat curl

ENV NODE_ENV=production
ENV PORT=8000

COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/prisma ./prisma
COPY --from=builder /app/data ./data

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["sh", "-c", "npx prisma db push --schema=prisma/schema.postgresql.prisma && npx tsx src/scripts/seed.ts && node dist/main.js"]
