<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 px-4 py-8">
    <div class="max-w-md w-full">
      <!-- Header -->
      <div class="text-center mb-8">
        <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          Create Your Account
        </h1>
        <p class="text-gray-600 dark:text-gray-400">
          Join AmStar Amateur Football Platform
        </p>
      </div>

      <!-- Form Card -->
      <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-8">
        <form @submit.prevent="handleRegister" class="space-y-5">
          <!-- Success Message -->
          <div
            v-if="success"
            class="bg-green-50 border-l-4 border-green-500 text-green-700 p-4 rounded-md"
            role="alert"
          >
            <p class="font-medium">Registration successful!</p>
            <p class="text-sm">Redirecting to login...</p>
          </div>

          <!-- Error Message -->
          <div
            v-if="error"
            class="bg-red-50 border-l-4 border-red-500 text-red-700 p-4 rounded-md"
            role="alert"
          >
            <p class="font-medium">{{ error }}</p>
          </div>

          <!-- Full Name -->
          <div>
            <label for="full_name" class="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
              Full Name
            </label>
            <input
              id="full_name"
              v-model="formData.full_name"
              type="text"
              class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white transition"
              placeholder="John Doe"
            />
          </div>

          <!-- Email -->
          <div>
            <label for="email" class="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
              Email Address <span class="text-red-500">*</span>
            </label>
            <input
              id="email"
              v-model="formData.email"
              type="email"
              required
              class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white transition"
              :class="{ 'border-red-500': emailError }"
              placeholder="you@example.com"
              @blur="validateEmail"
            />
            <p v-if="emailError" class="mt-1 text-sm text-red-600">{{ emailError }}</p>
          </div>

          <!-- Username -->
          <div>
            <label for="username" class="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
              Username <span class="text-red-500">*</span>
            </label>
            <input
              id="username"
              v-model="formData.username"
              type="text"
              required
              class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white transition"
              placeholder="johndoe"
            />
          </div>

          <!-- Password -->
          <div>
            <label for="password" class="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
              Password <span class="text-red-500">*</span>
            </label>
            <input
              id="password"
              v-model="formData.password"
              type="password"
              required
              minlength="6"
              class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white transition"
              :class="{ 'border-red-500': passwordError }"
              placeholder="••••••••"
              @input="validatePasswords"
            />
            <p class="mt-1 text-xs text-gray-500">Minimum 6 characters</p>
          </div>

          <!-- Confirm Password -->
          <div>
            <label for="confirmPassword" class="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
              Confirm Password <span class="text-red-500">*</span>
            </label>
            <input
              id="confirmPassword"
              v-model="confirmPassword"
              type="password"
              required
              class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:border-gray-600 dark:text-white transition"
              :class="{ 'border-red-500': passwordError }"
              placeholder="••••••••"
              @input="validatePasswords"
            />
            <p v-if="passwordError" class="mt-1 text-sm text-red-600">{{ passwordError }}</p>
          </div>

          <!-- Submit Button -->
          <button
            type="submit"
            :disabled="loading || !isFormValid"
            class="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold py-3 px-4 rounded-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl"
          >
            <span v-if="loading" class="flex items-center justify-center">
              <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Creating Account...
            </span>
            <span v-else>Create Account</span>
          </button>
        </form>

        <!-- Login Link -->
        <div class="mt-6 text-center">
          <p class="text-sm text-gray-600 dark:text-gray-400">
            Already have an account?
            <NuxtLink to="/auth/login" class="text-blue-600 hover:text-blue-700 font-semibold transition">
              Sign In
            </NuxtLink>
          </p>
        </div>
      </div>

      <!-- Back to Home -->
      <div class="text-center mt-6">
        <NuxtLink to="/" class="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition">
          ← Back to Home
        </NuxtLink>
      </div>
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

const confirmPassword = ref('')
const loading = ref(false)
const error = ref('')
const success = ref(false)
const emailError = ref('')
const passwordError = ref('')

const isFormValid = computed(() => {
  return (
    formData.value.email &&
    formData.value.username &&
    formData.value.password &&
    confirmPassword.value &&
    !emailError.value &&
    !passwordError.value
  )
})

const validateEmail = () => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (formData.value.email && !emailRegex.test(formData.value.email)) {
    emailError.value = 'Please enter a valid email address'
  } else {
    emailError.value = ''
  }
}

const validatePasswords = () => {
  if (formData.value.password && formData.value.password.length < 6) {
    passwordError.value = 'Password must be at least 6 characters'
  } else if (confirmPassword.value && formData.value.password !== confirmPassword.value) {
    passwordError.value = 'Passwords do not match'
  } else {
    passwordError.value = ''
  }
}

const handleRegister = async () => {
  // Final validation
  validateEmail()
  validatePasswords()

  if (emailError.value || passwordError.value) {
    console.log('Validation errors:', { emailError: emailError.value, passwordError: passwordError.value })
    return
  }

  loading.value = true
  error.value = ''
  success.value = false

  console.log('Attempting registration with:', {
    email: formData.value.email,
    username: formData.value.username,
    full_name: formData.value.full_name
  })

  const result = await register(formData.value)

  console.log('Registration result:', result)

  loading.value = false

  if (result.success) {
    success.value = true
    console.log('✅ Registration successful! Redirecting to login...')
    setTimeout(() => {
      router.push('/auth/login')
    }, 2000)
  } else {
    error.value = result.error || 'Registration failed. Please try again.'
    console.error('❌ Registration failed:', error.value)
  }
}
</script>
