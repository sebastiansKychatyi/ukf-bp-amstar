/**
 * Vuetify 3 Plugin for Nuxt 3
 *
 * This plugin initializes Vuetify with custom theme configuration
 * and integrates it with Nuxt's plugin system for SSR compatibility.
 *
 * @see https://vuetifyjs.com/en/getting-started/installation/#using-nuxt-3
 */

import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

// Vuetify styles (imported in nuxt.config.ts via css array)
// Icons are imported in nuxt.config.ts

/**
 * Professional Sports Theme for AmStar Football Platform
 * ======================================================
 * Primary: Football Green (#2E7D32) - Represents the football field
 * Secondary: Sports Blue (#1976D2) - Professional, clean, trustworthy
 */
const customLightTheme = {
  dark: false,
  colors: {
    primary: '#2E7D32',      // Football Green (grass field green)
    secondary: '#1976D2',    // Sports Blue (professional blue)
    accent: '#D32F2F',       // Red Card Red
    success: '#388E3C',      // Success Green
    warning: '#F57C00',      // Warning Orange
    error: '#D32F2F',        // Error Red
    info: '#0288D1',         // Info Blue
    background: '#FAFAFA',   // Light Gray Background
    surface: '#FFFFFF',      // White Surface
    'surface-variant': '#F5F5F5',  // Light Gray Variant
    'on-surface': '#212121', // Dark Text
    'on-primary': '#FFFFFF', // White Text on Primary
    'on-secondary': '#FFFFFF', // White Text on Secondary
  }
}

const customDarkTheme = {
  dark: true,
  colors: {
    primary: '#4CAF50',      // Lighter Green for dark mode
    secondary: '#42A5F5',    // Lighter Blue for dark mode
    accent: '#EF5350',       // Light Red
    success: '#66BB6A',      // Light Green
    warning: '#FFA726',      // Light Orange
    error: '#EF5350',        // Light Red
    info: '#29B6F6',         // Light Blue
    background: '#121212',   // Dark Background
    surface: '#1E1E1E',      // Dark Surface
    'surface-variant': '#2C2C2C', // Dark Gray Variant
    'on-surface': '#EEEEEE', // Light Text
    'on-primary': '#FFFFFF', // White Text
    'on-secondary': '#FFFFFF', // White Text
  }
}

export default defineNuxtPlugin((nuxtApp) => {
  const vuetify = createVuetify({
    // Enable all Vuetify components
    components,
    // Enable all Vuetify directives (v-ripple, v-scroll, etc.)
    directives,

    // SSR compatibility
    ssr: true,

    // Theme configuration
    theme: {
      defaultTheme: 'light',
      themes: {
        light: customLightTheme,
        dark: customDarkTheme,
      },
      variations: {
        colors: ['primary', 'secondary'],
        lighten: 2,
        darken: 2,
      }
    },

    // Global component defaults (consistent UI across app)
    defaults: {
      VCard: {
        elevation: 2,
        rounded: 'lg',
      },
      VBtn: {
        elevation: 0,
        rounded: 'lg',
        style: 'text-transform: none; font-weight: 600;',
      },
      VTextField: {
        variant: 'outlined',
        color: 'primary',
        density: 'comfortable',
      },
      VSelect: {
        variant: 'outlined',
        color: 'primary',
        density: 'comfortable',
      },
      VTextarea: {
        variant: 'outlined',
        color: 'primary',
      },
      VDataTable: {
        hover: true,
      },
      VAppBar: {
        elevation: 0,
      },
    },

    // Display breakpoints (matches Vuetify defaults)
    display: {
      mobileBreakpoint: 'sm',
      thresholds: {
        xs: 0,
        sm: 600,
        md: 960,
        lg: 1280,
        xl: 1920,
      },
    },
  })

  // Make Vuetify available in Nuxt app instance
  nuxtApp.vueApp.use(vuetify)
})
