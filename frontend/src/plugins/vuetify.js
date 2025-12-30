/**
 * Vuetify 3 Configuration
 * Sports/Professional Theme for AmStar Football Platform
 */

import '@mdi/font/css/materialdesignicons.css'
import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

// Custom sports theme colors
const lightTheme = {
  dark: false,
  colors: {
    primary: '#1E40AF', // Thunder Blue (matches backend team color)
    secondary: '#059669', // Field Green
    accent: '#DC2626', // Red Card Red
    success: '#10B981',
    warning: '#F59E0B',
    error: '#EF4444',
    info: '#3B82F6',
    background: '#F8FAFC',
    surface: '#FFFFFF',
    'surface-variant': '#F1F5F9',
    'on-surface': '#1E293B',
    'on-primary': '#FFFFFF',
    'on-secondary': '#FFFFFF',
  }
}

const darkTheme = {
  dark: true,
  colors: {
    primary: '#3B82F6', // Brighter blue for dark mode
    secondary: '#10B981',
    accent: '#F87171',
    success: '#34D399',
    warning: '#FBBF24',
    error: '#F87171',
    info: '#60A5FA',
    background: '#0F172A', // Deep dark blue
    surface: '#1E293B',
    'surface-variant': '#334155',
    'on-surface': '#F1F5F9',
    'on-primary': '#FFFFFF',
    'on-secondary': '#FFFFFF',
  }
}

export default createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: 'light',
    themes: {
      light: lightTheme,
      dark: darkTheme,
    },
    variations: {
      colors: ['primary', 'secondary'],
      lighten: 2,
      darken: 2,
    }
  },
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
  },
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
