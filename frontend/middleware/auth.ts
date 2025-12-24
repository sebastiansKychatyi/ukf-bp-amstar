export default defineNuxtRouteMiddleware((to, from) => {
  const { isAuthenticated } = useAuth()

  // If user is not authenticated and trying to access a protected route
  if (!isAuthenticated.value) {
    // Save the intended destination
    return navigateTo({
      path: '/auth/login',
      query: { redirect: to.fullPath }
    })
  }
})
