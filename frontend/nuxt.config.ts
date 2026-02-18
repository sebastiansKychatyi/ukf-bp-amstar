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
  // Disable SSR — this is an authenticated SPA dashboard; SSR adds no value
  // and causes Vuetify ID-counter hydration mismatches on v-data-table etc.
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
   * CRITICAL: These imports ensure Vuetify styles load during SSR
   */
  css: [
    'vuetify/styles',  // Vuetify base styles - REQUIRED for styling
    '@mdi/font/css/materialdesignicons.min.css',  // Material Design Icons
  ],

  /**
   * Build Configuration
   * ===================
   * Transpilation for SSR compatibility
   */
  build: {
    // CRITICAL: Transpile Vuetify for Node.js (SSR) compatibility
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
      // CRITICAL: Bundle Vuetify with SSR build (prevents module resolution errors)
      noExternal: ['vuetify'],
    },

    // Development server configuration
    server: {
      watch: {
        usePolling: true,  // Required for file watching in Docker/WSL
        interval: 1000,
      },
      hmr: {
        protocol: 'ws',
        host: 'localhost',
        port: 24678,
        clientPort: 24678,
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
