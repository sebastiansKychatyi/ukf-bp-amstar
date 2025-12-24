<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900">
    <!-- Global Navigation Header -->
    <AppHeader />

    <!-- Main Content -->
    <main>
      <NuxtPage />
    </main>
  </div>
</template>

<script setup lang="ts">
// Initialize auth on app mount
const { initAuth } = useAuth()

onMounted(() => {
  initAuth()
})
</script>
