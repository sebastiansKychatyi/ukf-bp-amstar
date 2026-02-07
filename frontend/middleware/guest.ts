/**
 * Guest Middleware — only allows unauthenticated users.
 * Redirects logged-in users away from login/register pages.
 */
export default defineNuxtRouteMiddleware((to, from) => {
  const { isAuthenticated } = useAuth()
  const token = useCookie('auth_token')

  if (isAuthenticated.value || token.value) {
    return navigateTo('/')
  }
})
