// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  devtools: { enabled: true },

  runtimeConfig: {
    public: {
      apiBaseUrl: process.env.NUXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1'
    }
  },

  app: {
    head: {
      title: 'AmStar - Amateur Football Platform',
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { name: 'description', content: 'Amateur Football Platform for challenges and ratings' }
      ]
    }
  },

  css: [
    '~/assets/css/main.css'
  ],

  postcss: {
    plugins: {
      tailwindcss: {},
      autoprefixer: {},
    },
  },

  // Development server configuration for Docker/Windows HMR
  vite: {
    server: {
      watch: {
        usePolling: true,
        interval: 1000,
      },
      hmr: {
        protocol: 'ws',
        host: 'localhost',
        port: 24678,
        clientPort: 24678,
      },
    },
  },

  compatibilityDate: '2024-12-24'
})
