/**
 * Middleware to restrict access to CAPTAIN role only
 */
export default defineNuxtRouteMiddleware((to, from) => {
  const { user, isAuthenticated } = useAuth()

  if (!isAuthenticated.value) {
    return navigateTo('/auth/login')
  }

  if (user.value?.role !== 'CAPTAIN') {
    return navigateTo({
      path: '/',
      query: { error: 'captain_required' }
    })
  }
})
