<template>
  <header class="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
    <nav class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between items-center h-16">
        <!-- Logo / Brand -->
        <div class="flex items-center">
          <NuxtLink to="/" class="flex items-center space-x-2">
            <svg class="h-8 w-8 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
            <span class="text-xl font-bold text-gray-900 dark:text-white">
              AmStar
            </span>
          </NuxtLink>
        </div>

        <!-- Navigation Links -->
        <div class="flex items-center space-x-4">
          <!-- Authenticated User -->
          <div v-if="isAuthenticated && user" class="flex items-center space-x-4">
            <!-- User Info -->
            <div class="hidden md:flex items-center space-x-3">
              <div class="h-8 w-8 rounded-full bg-blue-600 flex items-center justify-center">
                <span class="text-sm font-medium text-white">
                  {{ userInitials }}
                </span>
              </div>
              <div class="hidden lg:block">
                <p class="text-sm font-medium text-gray-900 dark:text-white">
                  {{ user.full_name || user.username }}
                </p>
                <p class="text-xs text-gray-500 dark:text-gray-400">
                  {{ user.email }}
                </p>
              </div>
            </div>

            <!-- Navigation Menu -->
            <NuxtLink
              to="/profile"
              class="text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 px-3 py-2 rounded-md text-sm font-medium transition"
            >
              Profile
            </NuxtLink>

            <!-- Logout Button -->
            <button
              @click="handleLogout"
              class="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition"
            >
              Logout
            </button>
          </div>

          <!-- Guest User -->
          <div v-else class="flex items-center space-x-3">
            <NuxtLink
              to="/auth/login"
              class="text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 px-4 py-2 rounded-lg text-sm font-medium transition"
            >
              Login
            </NuxtLink>
            <NuxtLink
              to="/auth/register"
              class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition shadow-sm"
            >
              Register
            </NuxtLink>
          </div>
        </div>
      </div>
    </nav>
  </header>
</template>

<script setup lang="ts">
const { user, isAuthenticated, logout } = useAuth()

const userInitials = computed(() => {
  if (user.value?.full_name) {
    return user.value.full_name
      .split(' ')
      .map(n => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2)
  }
  return user.value?.username?.slice(0, 2).toUpperCase() || 'U'
})

const handleLogout = () => {
  logout()
}

// Initialize auth when component mounts
onMounted(() => {
  const { initAuth } = useAuth()
  initAuth()
})
</script>
