/**
 * AmStar Football Platform - Main Entry Point
 */

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import vuetify from './plugins/vuetify'

// Create Vue application
const app = createApp(App)

// Create Pinia store
const pinia = createPinia()

// Use plugins
app.use(pinia)
app.use(router)
app.use(vuetify)

// Mount application
app.mount('#app')
