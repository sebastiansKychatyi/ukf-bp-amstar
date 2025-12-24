<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-100">
    <div class="text-center">
      <h1 class="text-4xl font-bold text-gray-900 mb-4">
        Welcome to AmStar
      </h1>
      <p class="text-xl text-gray-600 mb-8">
        Amateur Football Platform
      </p>
      <div class="space-y-4">
        <div class="bg-white p-6 rounded-lg shadow-md">
          <h2 class="text-2xl font-semibold mb-2">Status</h2>
          <p class="text-green-600">✓ Frontend Running</p>
          <p class="text-sm text-gray-500 mt-2">API: {{ apiUrl }}</p>
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

// Test API connection on mount
onMounted(async () => {
  try {
    const response = await $fetch(`${apiUrl.replace('/api/v1', '')}/health`)
    console.log('✓ Backend health check:', response)
  } catch (error) {
    console.error('✗ Backend health check failed:', error)
  }
})
</script>
