/**
 * Admin middleware — only allows access to users with is_superuser == true.
 * Redirects unauthenticated users to login, authenticated non-admins to dashboard.
 */
export default defineNuxtRouteMiddleware(() => {
  const { isAuthenticated, user } = useAuth()

  if (!isAuthenticated.value) {
    return navigateTo('/auth/login')
  }

  if (!user.value?.is_superuser) {
    return navigateTo('/dashboard')
  }
})
