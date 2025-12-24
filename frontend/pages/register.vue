<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-100 dark:bg-gray-900 px-4">
    <div class="max-w-md w-full bg-white dark:bg-gray-800 rounded-lg shadow-md p-8">
      <h1 class="text-2xl font-bold text-center text-gray-900 dark:text-white mb-6">
        Create Account
      </h1>

      <form @submit.prevent="handleRegister" class="space-y-4">
        <div v-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {{ error }}
        </div>

        <div v-if="success" class="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded">
          Registration successful! Redirecting to login...
        </div>

        <div>
          <label for="email" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Email
          </label>
          <input
            id="email"
            v-model="formData.email"
            type="email"
            required
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            placeholder="you@example.com"
          />
        </div>

        <div>
          <label for="username" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Username
          </label>
          <input
            id="username"
            v-model="formData.username"
            type="text"
            required
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            placeholder="username"
          />
        </div>

        <div>
          <label for="full_name" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Full Name
          </label>
          <input
            id="full_name"
            v-model="formData.full_name"
            type="text"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            placeholder="John Doe"
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
          {{ loading ? 'Creating Account...' : 'Register' }}
        </button>
      </form>

      <p class="mt-4 text-center text-sm text-gray-600 dark:text-gray-400">
        Already have an account?
        <NuxtLink to="/login" class="text-blue-600 hover:text-blue-700 font-medium">
          Login
        </NuxtLink>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
const { register } = useAuth()
const router = useRouter()

const formData = ref({
  email: '',
  username: '',
  full_name: '',
  password: '',
})

const loading = ref(false)
const error = ref('')
const success = ref(false)

const handleRegister = async () => {
  loading.value = true
  error.value = ''
  success.value = false

  const result = await register(formData.value)

  loading.value = false

  if (result.success) {
    success.value = true
    setTimeout(() => {
      router.push('/login')
    }, 2000)
  } else {
    error.value = result.error || 'Registration failed'
  }
}
</script>
