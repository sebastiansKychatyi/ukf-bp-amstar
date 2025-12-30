# =========================================================
# AmStar Frontend - Optimized Multi-Stage Docker Build
# Nuxt 3 + Vuetify 3 + Vue 3
# Node.js 20 LTS (Iron) - Required for Nuxt 3.13+ ecosystem
# =========================================================

# ============ BUILD STAGE ============
# Install dependencies and build the application
# Using Node.js 20 LTS to satisfy engine requirements (>=20.19.0)
FROM node:20-alpine AS build

WORKDIR /app

# Copy dependency manifests first (Docker layer caching optimization)
COPY package*.json ./

# Install ALL dependencies (devDependencies needed for Nuxt build)
# Using `npm ci` for reproducible builds (respects package-lock.json)
RUN npm ci

# Copy application source code
COPY . .

# Prepare Nuxt environment (generates .nuxt directory, type definitions)
# This runs automatically via "postinstall" script, but explicit for clarity
RUN npm run postinstall

# Build Nuxt application for production
# Creates optimized .output directory with SSR server and static assets
RUN npm run build

# ============ PRODUCTION STAGE ============
# Minimal runtime image with only production dependencies
# Using Node.js 20 LTS to match build stage and satisfy runtime requirements
FROM node:20-alpine AS production

WORKDIR /app

# Install dumb-init for proper signal handling (graceful shutdowns)
RUN apk add --no-cache dumb-init

# Create non-root user for security
RUN addgroup -g 1001 -S nodejs && adduser -S nuxtjs -u 1001

# Copy package files for production dependency installation
COPY package*.json ./

# Install ONLY production dependencies (smaller image size)
RUN npm ci --only=production

# Copy built application from build stage
# .output contains the entire server + client bundle
COPY --from=build --chown=nuxtjs:nodejs /app/.output /app/.output

# Switch to non-root user
USER nuxtjs

# Expose Nuxt default port
EXPOSE 3000

# Environment variables
ENV NODE_ENV=production
ENV NUXT_HOST=0.0.0.0
ENV NUXT_PORT=3000

# Health check (checks root path instead of /api/health)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD node -e "require('http').get('http://localhost:3000/', (r) => {process.exit(r.statusCode === 200 ? 0 : 1)})" || exit 1

# Start Nuxt.js SSR server with dumb-init
CMD ["dumb-init", "node", ".output/server/index.mjs"]
