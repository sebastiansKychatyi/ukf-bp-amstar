<template>
  <v-card elevation="2">
    <v-card-title>
      <v-icon class="mr-2">mdi-bell</v-icon>
      Recent Notifications
      <v-chip v-if="unreadCount > 0" size="small" color="error" class="ml-2">
        {{ unreadCount }}
      </v-chip>
    </v-card-title>
    <v-card-text>
      <div v-if="loading" class="text-center pa-4">
        <v-progress-circular indeterminate color="primary" size="24" />
      </div>
      <div v-else-if="notifications.length === 0" class="text-center text-medium-emphasis pa-6">
        No notifications
      </div>
      <v-list v-else density="compact">
        <v-list-item
          v-for="n in notifications"
          :key="n.id"
          :class="{ 'bg-blue-lighten-5': !n.is_read }"
          class="mb-1 rounded"
        >
          <template #prepend>
            <v-icon :icon="getIcon(n.type)" :color="getColor(n.type)" size="small" class="mr-2" />
          </template>
          <v-list-item-title class="text-body-2 font-weight-medium">
            {{ n.title }}
          </v-list-item-title>
          <v-list-item-subtitle class="text-caption">
            {{ n.message }}
          </v-list-item-subtitle>
          <template #append>
            <span class="text-caption text-medium-emphasis">
              {{ timeAgo(n.created_at) }}
            </span>
          </template>
        </v-list-item>
      </v-list>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
const props = defineProps<{
  notifications: any[]
  loading: boolean
}>()

const unreadCount = computed(() => props.notifications.filter(n => !n.is_read).length)

const getIcon = (type: string) => {
  const icons: Record<string, string> = {
    challenge_received: 'mdi-sword-cross',
    challenge_accepted: 'mdi-check-circle',
    challenge_rejected: 'mdi-close-circle',
    challenge_cancelled: 'mdi-cancel',
    challenge_completed: 'mdi-trophy',
    join_request_received: 'mdi-account-plus',
    join_request_accepted: 'mdi-account-check',
    join_request_rejected: 'mdi-account-remove',
    rating_changed: 'mdi-chart-line',
  }
  return icons[type] || 'mdi-bell'
}

const getColor = (type: string) => {
  const colors: Record<string, string> = {
    challenge_received: 'warning',
    challenge_accepted: 'success',
    challenge_rejected: 'error',
    challenge_cancelled: 'grey',
    challenge_completed: 'primary',
    join_request_received: 'info',
    join_request_accepted: 'success',
    join_request_rejected: 'error',
    rating_changed: 'primary',
  }
  return colors[type] || 'grey'
}

const timeAgo = (dateStr: string) => {
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'now'
  if (mins < 60) return `${mins}m`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h`
  const days = Math.floor(hours / 24)
  return `${days}d`
}
</script>
