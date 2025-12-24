export default defineNuxtRouteMiddleware((to, from) => {
  const { isAuthenticated } = useAuth()

  // If user is authenticated and trying to access auth pages (login/register)
  // redirect them to the home page
  if (isAuthenticated.value) {
    return navigateTo('/')
  }
})
