/**
 * Middleware to restrict access to REFEREE role only
 */
export default defineNuxtRouteMiddleware((to, from) => {
  const { user, isAuthenticated } = useAuth()

  if (!isAuthenticated.value) {
    return navigateTo('/auth/login')
  }

  if (user.value?.role !== 'REFEREE') {
    return navigateTo({
      path: '/',
      query: { error: 'referee_required' }
    })
  }
})
