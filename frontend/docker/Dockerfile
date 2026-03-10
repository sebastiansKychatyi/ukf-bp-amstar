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

# Build Nuxt application for production
# nuxi prepare (postinstall) already ran during npm ci above
# Creates optimized .output directory with SSR server and static assets
RUN npm run build

# ============ PRODUCTION STAGE ============
# Nuxt's .output bundle is fully self-contained — no npm packages are needed
# at runtime.  Copying .output alone is sufficient; running npm ci here would
# trigger the postinstall script (nuxi prepare) which fails because nuxi is a
# devDependency excluded by --only=production.
FROM node:20-alpine AS production

WORKDIR /app

# Install dumb-init for proper signal handling (graceful shutdowns)
RUN apk add --no-cache dumb-init

# Create non-root user for security
RUN addgroup -g 1001 -S nodejs && adduser -S nuxtjs -u 1001

# Copy built application from build stage.
# .output contains the entire server + client bundle with all dependencies
# pre-bundled by Nitro — no node_modules directory is required.
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
