# =============================================================
# Stage 1: Dependencies - install pnpm and project dependencies
# =============================================================
FROM node:20-alpine AS deps

WORKDIR /app

# Enable corepack for pnpm support
RUN corepack enable && corepack prepare pnpm@latest --activate

# Copy dependency manifests only (maximise layer cache)
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml* ./

# Install production + dev dependencies (dev needed for build)
RUN pnpm install --frozen-lockfile

# =============================================================
# Stage 2: Build - compile Next.js standalone output
# =============================================================
FROM node:20-alpine AS builder

WORKDIR /app

RUN corepack enable && corepack prepare pnpm@latest --activate

# Copy installed node_modules from deps stage
COPY --from=deps /app/node_modules ./node_modules
COPY --from=deps /app/package.json ./package.json

# Copy all source code
COPY . .

# Build-time environment variables (baked into the JS bundle)
ARG NEXT_PUBLIC_API_URL
ARG NEXT_PUBLIC_TOSS_CLIENT_KEY
ARG NEXT_PUBLIC_KAKAO_MAP_KEY
ARG BACKEND_URL=http://localhost:8000

ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
ENV NEXT_PUBLIC_TOSS_CLIENT_KEY=${NEXT_PUBLIC_TOSS_CLIENT_KEY}
ENV NEXT_PUBLIC_KAKAO_MAP_KEY=${NEXT_PUBLIC_KAKAO_MAP_KEY}
ENV BACKEND_URL=${BACKEND_URL}

# Disable Next.js telemetry during build
ENV NEXT_TELEMETRY_DISABLED=1

# Build the application (produces .next/standalone/)
RUN pnpm build

# =============================================================
# Stage 3: Runner - minimal production image
# =============================================================
FROM node:20-alpine AS runner

WORKDIR /app

# Install wget for healthcheck (curl not available on alpine by default)
RUN apk add --no-cache wget

ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME=0.0.0.0
ENV NEXT_TELEMETRY_DISABLED=1

# Create non-root user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 --ingroup nodejs nextjs

# Copy public assets to standalone directory
COPY --from=builder --chown=nextjs:nodejs /app/public ./public

# Copy standalone server output
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
# Copy static assets into the standalone .next directory
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Switch to non-root user
USER nextjs

# Expose port
EXPOSE 3000

# Health check - verify the app responds
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/ || exit 1

# Start the standalone Next.js server
CMD ["node", "server.js"]
