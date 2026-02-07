/**
 * Auth Initialization Plugin
 * ==========================
 * Restores user state from the JWT cookie on every page load,
 * BEFORE Nuxt route middleware executes.
 *
 * Without this plugin, role-based middleware (captain.ts, referee.ts)
 * would see user.value === null on hard refresh and wrongly redirect.
 */
export default defineNuxtPlugin(async () => {
  const { initAuth } = useAuth()
  await initAuth()
})
