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
        <div class="hidden md:flex items-center space-x-1">
          <NuxtLink
            v-for="link in navLinks"
            :key="link.to"
            :to="link.to"
            class="text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 px-3 py-2 rounded-md text-sm font-medium transition"
          >
            {{ link.label }}
          </NuxtLink>
        </div>

        <!-- User Section -->
        <div class="flex items-center space-x-4">
          <!-- Authenticated User -->
          <div v-if="isAuthenticated && user" class="flex items-center space-x-3">
            <!-- Notification Bell -->
            <div class="relative">
              <button
                @click="toggleNotifications"
                class="relative p-2 text-gray-500 hover:text-blue-600 transition rounded-full hover:bg-gray-100"
              >
                <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                </svg>
                <span
                  v-if="unreadCount > 0"
                  class="absolute -top-1 -right-1 inline-flex items-center justify-center w-5 h-5 text-xs font-bold text-white bg-red-500 rounded-full"
                >
                  {{ unreadCount > 9 ? '9+' : unreadCount }}
                </span>
              </button>

              <!-- Notification Dropdown -->
              <div
                v-if="showNotifications"
                class="absolute right-0 mt-2 w-80 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-50 max-h-96 overflow-y-auto"
              >
                <div class="flex items-center justify-between p-3 border-b border-gray-200 dark:border-gray-700">
                  <span class="font-medium text-sm text-gray-900 dark:text-white">Notifications</span>
                  <button
                    v-if="unreadCount > 0"
                    @click="markAllRead"
                    class="text-xs text-blue-600 hover:text-blue-800"
                  >
                    Mark all read
                  </button>
                </div>

                <div v-if="notifItems.length === 0" class="p-6 text-center text-sm text-gray-500">
                  No notifications
                </div>

                <div v-else>
                  <div
                    v-for="n in notifItems"
                    :key="n.id"
                    class="px-3 py-2 border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer"
                    :class="{ 'bg-blue-50 dark:bg-blue-900/20': !n.is_read }"
                  >
                    <div class="flex items-start space-x-2">
                      <span class="text-lg mt-0.5">{{ getEmoji(n.type) }}</span>
                      <div class="flex-1 min-w-0">
                        <p class="text-sm font-medium text-gray-900 dark:text-white truncate">
                          {{ n.title }}
                        </p>
                        <p class="text-xs text-gray-500 dark:text-gray-400">
                          {{ n.message }}
                        </p>
                        <p class="text-xs text-gray-400 mt-0.5">
                          {{ timeAgo(n.created_at) }}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                <div class="p-2 border-t border-gray-200 dark:border-gray-700">
                  <NuxtLink
                    to="/dashboard"
                    class="block text-center text-sm text-blue-600 hover:text-blue-800 py-1"
                    @click="showNotifications = false"
                  >
                    View all on Dashboard
                  </NuxtLink>
                </div>
              </div>
            </div>

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
                  {{ user.role }}
                </p>
              </div>
            </div>

            <NuxtLink
              to="/dashboard"
              class="text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 px-3 py-2 rounded-md text-sm font-medium transition"
            >
              Dashboard
            </NuxtLink>

            <NuxtLink
              to="/profile"
              class="text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 px-3 py-2 rounded-md text-sm font-medium transition"
            >
              Profile
            </NuxtLink>

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
const { user, isAuthenticated, isCaptain, logout } = useAuth()
const config = useRuntimeConfig()
const apiBase = computed(() => config.public.apiBaseUrl || 'http://localhost:8000/api/v1')

const getAuthHeaders = () => {
  const token = useCookie('auth_token')
  return token.value ? { Authorization: `Bearer ${token.value}` } : {}
}

const navLinks = computed(() => {
  const links = [
    { label: 'Teams', to: '/teams' },
    { label: 'Players', to: '/players' },
    { label: 'Challenges', to: '/challenges' },
    { label: 'Leaderboard', to: '/leaderboard' },
  ]
  if (isCaptain.value) {
    links.push({ label: 'Find Opponent', to: '/matchmaking' })
  }
  return links
})

const userInitials = computed(() => {
  if (user.value?.full_name) {
    return user.value.full_name
      .split(' ')
      .map((n: string) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2)
  }
  return user.value?.username?.slice(0, 2).toUpperCase() || 'U'
})

// ── Notifications ──
const showNotifications = ref(false)
const unreadCount = ref(0)
const notifItems = ref<any[]>([])

const toggleNotifications = () => {
  showNotifications.value = !showNotifications.value
  if (showNotifications.value) {
    fetchNotifications()
  }
}

const fetchNotifications = async () => {
  try {
    const data = await $fetch<any>(`${apiBase.value}/notifications/`, {
      headers: getAuthHeaders(),
      params: { limit: 10 },
    })
    notifItems.value = data.items || []
    unreadCount.value = data.unread_count || 0
  } catch {
    notifItems.value = []
  }
}

const fetchUnreadCount = async () => {
  try {
    const data = await $fetch<any>(`${apiBase.value}/notifications/unread-count`, {
      headers: getAuthHeaders(),
    })
    unreadCount.value = data.unread_count || 0
  } catch {
    unreadCount.value = 0
  }
}

const markAllRead = async () => {
  try {
    await $fetch(`${apiBase.value}/notifications/read-all`, {
      method: 'PUT',
      headers: getAuthHeaders(),
    })
    unreadCount.value = 0
    notifItems.value = notifItems.value.map(n => ({ ...n, is_read: true }))
  } catch { /* ignore */ }
}

const getEmoji = (type: string) => {
  const emojis: Record<string, string> = {
    challenge_received: '\u2694\uFE0F',
    challenge_accepted: '\u2705',
    challenge_rejected: '\u274C',
    challenge_cancelled: '\u26D4',
    challenge_completed: '\uD83C\uDFC6',
    join_request_received: '\uD83D\uDCE9',
    join_request_accepted: '\uD83C\uDF89',
    join_request_rejected: '\uD83D\uDEAB',
    rating_changed: '\uD83D\uDCC8',
  }
  return emojis[type] || '\uD83D\uDD14'
}

const timeAgo = (dateStr: string) => {
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}

// Close dropdown on outside click
const onClickOutside = (e: Event) => {
  if (showNotifications.value) {
    showNotifications.value = false
  }
}

const handleLogout = () => {
  logout()
}

onMounted(() => {
  const { initAuth } = useAuth()
  initAuth()

  // Poll unread count every 30 seconds when authenticated
  if (isAuthenticated.value) {
    fetchUnreadCount()
    const interval = setInterval(() => {
      if (isAuthenticated.value) {
        fetchUnreadCount()
      } else {
        clearInterval(interval)
      }
    }, 30000)
  }
})
</script>
