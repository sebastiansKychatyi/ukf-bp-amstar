/**
 * Nuxt 3 Configuration
 * ====================
 * Configuration file for the AmStar Football Platform frontend
 *
 * Key Features:
 * - Vuetify 3 UI framework integration
 * - SSR (Server-Side Rendering) support
 * - Environment-based API configuration
 * - Material Design Icons
 *
 * @see https://nuxt.com/docs/api/configuration/nuxt-config
 */

export default defineNuxtConfig({
  // SSR disabled: this is a client-side SPA dashboard.
  // Enabling SSR causes Vuetify ID-counter hydration mismatches on v-data-table.
  ssr: false,

  // Enable Nuxt DevTools for development
  devtools: { enabled: true },

  /**
   * Runtime Configuration
   * ====================
   * Environment variables accessible in both server and client
   */
  runtimeConfig: {
    public: {
      // API base URL - defaults to localhost, override with env var
      apiBaseUrl: process.env.NUXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1'
    }
  },

  /**
   * Application Metadata
   * ===================
   * SEO and browser configuration
   */
  app: {
    head: {
      title: 'AmStar - Amateur Football Platform',
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { name: 'description', content: 'Amateur Football Platform for team management, challenges, and player ratings' }
      ],
      link: [
        // Material Design Icons - CDN fallback for SSR
        {
          rel: 'stylesheet',
          href: 'https://cdn.jsdelivr.net/npm/@mdi/font@latest/css/materialdesignicons.min.css'
        }
      ]
    }
  },

  /**
   * Global CSS Imports
   * ==================
   * These imports ensure Vuetify styles are bundled at build time.
   */
  css: [
    'vuetify/styles',  // Vuetify base styles
    '@mdi/font/css/materialdesignicons.min.css',  // Material Design Icons
  ],

  /**
   * Build Configuration
   * ===================
   * Transpilation for SSR compatibility
   */
  build: {
    // Transpile Vuetify for Node.js compatibility
    transpile: ['vuetify'],
  },

  /**
   * Vite Configuration
   * ==================
   * Build tool settings
   */
  vite: {
    // SSR build options
    ssr: {
      // Bundle Vuetify with the SSR build to prevent module resolution errors
      noExternal: ['vuetify'],
    },

    // Development server configuration
    server: {
      watch: {
        usePolling: true,  // Polling required for reliable file watching in Docker/WSL environments
        interval: 1000,
      },
      // Explicit HMR config prevents WebSocket connection failures on Windows/WSL2.
      // Port 24678 is the Vite HMR fallback port; clientPort tells the browser
      // where to connect. Both must match for hot-reload to work reliably.
      hmr: {
        protocol: 'ws',
        host: 'localhost',

      },
    },

    // Disable debug logs in production
    define: {
      'process.env.DEBUG': false,
    },
  },

  // Nuxt 3 compatibility date
  compatibilityDate: '2024-12-24'
})
