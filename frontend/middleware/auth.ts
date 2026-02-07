/**
 * Auth Middleware — requires authenticated user.
 * Checks both the cookie token and the reactive auth state.
 * Saves the intended destination so login can redirect back.
 */
export default defineNuxtRouteMiddleware((to, from) => {
  const { isAuthenticated } = useAuth()
  const token = useCookie('auth_token')

  if (!isAuthenticated.value && !token.value) {
    return navigateTo({
      path: '/auth/login',
      query: { redirect: to.fullPath },
    })
  }
})
