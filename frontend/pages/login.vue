<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-100 dark:bg-gray-900 px-4">
    <div class="max-w-md w-full bg-white dark:bg-gray-800 rounded-lg shadow-md p-8">
      <h1 class="text-2xl font-bold text-center text-gray-900 dark:text-white mb-6">
        Login to AmStar
      </h1>

      <form @submit.prevent="handleLogin" class="space-y-4">
        <div v-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {{ error }}
        </div>

        <div>
          <label for="username" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Email
          </label>
          <input
            id="username"
            v-model="formData.username"
            type="email"
            required
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            placeholder="you@example.com"
          />
        </div>

        <div>
          <label for="password" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Password
          </label>
          <input
            id="password"
            v-model="formData.password"
            type="password"
            required
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            placeholder="••••••••"
          />
        </div>

        <button
          type="submit"
          :disabled="loading"
          class="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ loading ? 'Logging in...' : 'Login' }}
        </button>
      </form>

      <p class="mt-4 text-center text-sm text-gray-600 dark:text-gray-400">
        Don't have an account?
        <NuxtLink to="/register" class="text-blue-600 hover:text-blue-700 font-medium">
          Register
        </NuxtLink>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
const { login } = useAuth()
const router = useRouter()

const formData = ref({
  username: '',
  password: '',
})

const loading = ref(false)
const error = ref('')

const handleLogin = async () => {
  loading.value = true
  error.value = ''

  const result = await login(formData.value)

  loading.value = false

  if (result.success) {
    router.push('/')
  } else {
    error.value = result.error || 'Login failed'
  }
}
</script>
