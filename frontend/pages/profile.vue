<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900">
    <!-- Navigation Bar -->
    <nav class="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center h-16">
          <div class="flex items-center">
            <NuxtLink to="/" class="text-xl font-bold text-gray-900 dark:text-white">
              AmStar
            </NuxtLink>
          </div>
          <div class="flex items-center space-x-4">
            <span class="text-sm text-gray-700 dark:text-gray-300">
              {{ user?.email }}
            </span>
            <button
              @click="handleLogout"
              class="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg transition text-sm font-medium"
            >
              Logout
            </button>
          </div>
        </div>
      </div>
    </nav>

    <!-- Main Content -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- Profile Header -->
      <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-lg overflow-hidden mb-6">
        <div class="bg-gradient-to-r from-blue-600 to-indigo-600 h-32"></div>
        <div class="px-8 pb-8">
          <div class="flex items-end space-x-5 -mt-12">
            <div class="flex-shrink-0">
              <div class="h-24 w-24 rounded-full bg-white dark:bg-gray-700 border-4 border-white dark:border-gray-800 flex items-center justify-center">
                <span class="text-3xl font-bold text-blue-600 dark:text-blue-400">
                  {{ initials }}
                </span>
              </div>
            </div>
            <div class="flex-1 min-w-0 py-2">
              <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
                {{ user?.full_name || user?.username }}
              </h1>
              <p class="text-gray-600 dark:text-gray-400">
                @{{ user?.username }}
              </p>
            </div>
            <div class="flex-shrink-0 py-2">
              <span
                v-if="user?.is_active"
                class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300"
              >
                <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                </svg>
                Active
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Profile Information -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- User Details Card -->
        <div class="lg:col-span-2">
          <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6">
            <h2 class="text-xl font-bold text-gray-900 dark:text-white mb-6">
              Account Information
            </h2>
            <div class="space-y-4">
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <p class="text-sm font-medium text-gray-500 dark:text-gray-400">Full Name</p>
                  <p class="mt-1 text-base text-gray-900 dark:text-white">
                    {{ user?.full_name || 'Not set' }}
                  </p>
                </div>
                <div>
                  <p class="text-sm font-medium text-gray-500 dark:text-gray-400">Username</p>
                  <p class="mt-1 text-base text-gray-900 dark:text-white">
                    {{ user?.username }}
                  </p>
                </div>
              </div>
              <div>
                <p class="text-sm font-medium text-gray-500 dark:text-gray-400">Email Address</p>
                <p class="mt-1 text-base text-gray-900 dark:text-white">
                  {{ user?.email }}
                </p>
              </div>
              <div>
                <p class="text-sm font-medium text-gray-500 dark:text-gray-400">User ID</p>
                <p class="mt-1 text-base text-gray-900 dark:text-white font-mono">
                  #{{ user?.id }}
                </p>
              </div>
              <div>
                <p class="text-sm font-medium text-gray-500 dark:text-gray-400">Member Since</p>
                <p class="mt-1 text-base text-gray-900 dark:text-white">
                  {{ formatDate(user?.created_at) }}
                </p>
              </div>
            </div>
          </div>
        </div>

        <!-- Quick Stats Card -->
        <div class="lg:col-span-1">
          <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6">
            <h2 class="text-xl font-bold text-gray-900 dark:text-white mb-6">
              Account Status
            </h2>
            <div class="space-y-4">
              <div class="flex items-center justify-between">
                <span class="text-sm text-gray-600 dark:text-gray-400">Account Type</span>
                <span class="text-sm font-medium text-gray-900 dark:text-white">
                  {{ user?.is_superuser ? 'Admin' : 'User' }}
                </span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-sm text-gray-600 dark:text-gray-400">Status</span>
                <span class="text-sm font-medium" :class="user?.is_active ? 'text-green-600' : 'text-red-600'">
                  {{ user?.is_active ? 'Active' : 'Inactive' }}
                </span>
              </div>
            </div>
          </div>

          <!-- Quick Actions -->
          <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6 mt-6">
            <h2 class="text-xl font-bold text-gray-900 dark:text-white mb-4">
              Quick Actions
            </h2>
            <div class="space-y-2">
              <button class="w-full text-left px-4 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 transition">
                Edit Profile
              </button>
              <button class="w-full text-left px-4 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 transition">
                Change Password
              </button>
              <button class="w-full text-left px-4 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 transition">
                Notification Settings
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  middleware: 'auth'
})

const { user, logout } = useAuth()
const router = useRouter()

const initials = computed(() => {
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

const formatDate = (dateString: string | undefined) => {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

const handleLogout = () => {
  logout()
}
</script>
