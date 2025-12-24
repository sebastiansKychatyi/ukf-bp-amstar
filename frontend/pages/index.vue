<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-100 dark:bg-gray-900">
    <div class="text-center max-w-2xl mx-auto px-4">
      <h1 class="text-4xl font-bold text-gray-900 dark:text-white mb-4">
        Welcome to AmStar
      </h1>
      <p class="text-xl text-gray-600 dark:text-gray-400 mb-8">
        Amateur Football Platform
      </p>

      <div class="space-y-4">
        <!-- User Status -->
        <div class="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md">
          <h2 class="text-2xl font-semibold text-gray-900 dark:text-white mb-4">
            {{ isAuthenticated ? 'Welcome!' : 'Get Started' }}
          </h2>

          <div v-if="isAuthenticated && user" class="space-y-3">
            <p class="text-green-600 dark:text-green-400 text-lg">
              ✓ Logged in as {{ user.full_name || user.username }}
            </p>
            <p class="text-sm text-gray-600 dark:text-gray-400">
              Email: {{ user.email }}
            </p>
            <button
              @click="logout"
              class="mt-4 bg-red-600 hover:bg-red-700 text-white px-6 py-2 rounded-lg transition"
            >
              Logout
            </button>
          </div>

          <div v-else class="space-y-3">
            <p class="text-gray-600 dark:text-gray-400 mb-4">
              Please login or create an account to get started
            </p>
            <div class="flex gap-4 justify-center">
              <NuxtLink
                to="/login"
                class="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg transition"
              >
                Login
              </NuxtLink>
              <NuxtLink
                to="/register"
                class="bg-green-600 hover:bg-green-700 text-white px-6 py-2 rounded-lg transition"
              >
                Register
              </NuxtLink>
            </div>
          </div>
        </div>

        <!-- System Status -->
        <div class="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md">
          <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-2">System Status</h2>
          <p class="text-green-600 dark:text-green-400">✓ Frontend Running</p>
          <p class="text-sm text-gray-500 dark:text-gray-400 mt-2">API: {{ apiUrl }}</p>
        </div>

        <a
          href="http://localhost:8000/docs"
          target="_blank"
          class="inline-block bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition"
        >
          View API Documentation
        </a>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const config = useRuntimeConfig()
const apiUrl = config.public.apiBaseUrl
const { user, isAuthenticated, initAuth, logout } = useAuth()

// Initialize auth and test API connection on mount
onMounted(async () => {
  initAuth()

  try {
    const response = await $fetch(`${apiUrl.replace('/api/v1', '')}/health`)
    console.log('✓ Backend health check:', response)
  } catch (error) {
    console.error('✗ Backend health check failed:', error)
  }
})
</script>
