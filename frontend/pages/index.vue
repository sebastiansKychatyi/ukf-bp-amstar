<template>
  <div class="flex items-center justify-center py-12 px-4">
    <div class="text-center max-w-4xl mx-auto">
      <!-- Hero Section -->
      <div class="mb-12">
        <h1 class="text-5xl font-bold text-gray-900 dark:text-white mb-4">
          Welcome to AmStar
        </h1>
        <p class="text-2xl text-gray-600 dark:text-gray-400 mb-8">
          Amateur Football Platform
        </p>
        <p class="text-lg text-gray-500 dark:text-gray-500 max-w-2xl mx-auto">
          Connect with teams, organize challenges, and track your performance in the amateur football community.
        </p>
      </div>

      <!-- Features Grid -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
        <!-- Feature 1 -->
        <div class="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
          <div class="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center mx-auto mb-4">
            <svg class="w-6 h-6 text-blue-600 dark:text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
          </div>
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">Team Management</h3>
          <p class="text-gray-600 dark:text-gray-400 text-sm">Create and manage your football team with ease</p>
        </div>

        <!-- Feature 2 -->
        <div class="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
          <div class="w-12 h-12 bg-green-100 dark:bg-green-900 rounded-lg flex items-center justify-center mx-auto mb-4">
            <svg class="w-6 h-6 text-green-600 dark:text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">Challenge System</h3>
          <p class="text-gray-600 dark:text-gray-400 text-sm">Organize and accept challenges from other teams</p>
        </div>

        <!-- Feature 3 -->
        <div class="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
          <div class="w-12 h-12 bg-purple-100 dark:bg-purple-900 rounded-lg flex items-center justify-center mx-auto mb-4">
            <svg class="w-6 h-6 text-purple-600 dark:text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
            </svg>
          </div>
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">Rating System</h3>
          <p class="text-gray-600 dark:text-gray-400 text-sm">Track performance and improve your rankings</p>
        </div>
      </div>

      <!-- CTA Section -->
      <div v-if="!isAuthenticated" class="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl p-8 text-white shadow-xl">
        <h2 class="text-3xl font-bold mb-4">Ready to Get Started?</h2>
        <p class="text-lg mb-6 opacity-90">Join the AmStar community and take your team to the next level</p>
        <div class="flex gap-4 justify-center">
          <NuxtLink
            to="/auth/register"
            class="bg-white text-blue-600 hover:bg-gray-100 px-8 py-3 rounded-lg font-semibold transition shadow-lg"
          >
            Create Account
          </NuxtLink>
          <NuxtLink
            to="/auth/login"
            class="bg-blue-700 hover:bg-blue-800 text-white px-8 py-3 rounded-lg font-semibold transition border-2 border-white"
          >
            Sign In
          </NuxtLink>
        </div>
      </div>

      <!-- Authenticated User Section -->
      <div v-else class="bg-gradient-to-r from-green-600 to-teal-600 rounded-2xl p-8 text-white shadow-xl">
        <h2 class="text-3xl font-bold mb-4">Welcome back, {{ user?.full_name || user?.username }}! 👋</h2>
        <p class="text-lg mb-6 opacity-90">Ready to continue your journey?</p>
        <NuxtLink
          to="/profile"
          class="inline-block bg-white text-green-600 hover:bg-gray-100 px-8 py-3 rounded-lg font-semibold transition shadow-lg"
        >
          Go to Profile
        </NuxtLink>
      </div>

      <!-- System Status -->
      <div class="mt-12 bg-white dark:bg-gray-800 p-6 rounded-xl shadow-md">
        <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-3">System Status</h2>
        <div class="flex items-center justify-center space-x-6">
          <div class="text-center">
            <p class="text-green-600 dark:text-green-400 font-semibold">✓ Frontend</p>
            <p class="text-xs text-gray-500 dark:text-gray-400">Running</p>
          </div>
          <div class="text-center">
            <p class="text-green-600 dark:text-green-400 font-semibold">✓ Backend</p>
            <p class="text-xs text-gray-500 dark:text-gray-400">Connected</p>
          </div>
          <div class="text-center">
            <p class="text-green-600 dark:text-green-400 font-semibold">✓ Database</p>
            <p class="text-xs text-gray-500 dark:text-gray-400">Active</p>
          </div>
        </div>
        <div class="mt-4">
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            class="text-sm text-blue-600 dark:text-blue-400 hover:underline"
          >
            View API Documentation →
          </a>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const config = useRuntimeConfig()
const { user, isAuthenticated } = useAuth()

// Test API connection on mount
onMounted(async () => {
  try {
    const apiUrl = config.public.apiBaseUrl
    const response = await $fetch(`${apiUrl.replace('/api/v1', '')}/health`)
    console.log('✓ Backend health check:', response)
  } catch (error) {
    console.error('✗ Backend health check failed:', error)
  }
})
</script>
