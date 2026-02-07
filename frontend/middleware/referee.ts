/**
 * Referee Middleware — requires REFEREE role.
 * First checks authentication, then verifies the user role.
 */
export default defineNuxtRouteMiddleware((to, from) => {
  const { user, isAuthenticated } = useAuth()
  const token = useCookie('auth_token')

  if (!isAuthenticated.value && !token.value) {
    return navigateTo({
      path: '/auth/login',
      query: { redirect: to.fullPath },
    })
  }

  if (user.value && user.value.role !== 'REFEREE') {
    return navigateTo({
      path: '/',
      query: { error: 'referee_required' },
    })
  }
})
