import { ref, computed } from 'vue'

interface User {
  id: number
  email: string
  username: string
  full_name: string | null
  is_active: boolean
  is_superuser: boolean
}

interface LoginCredentials {
  username: string
  password: string
}

interface RegisterData {
  email: string
  username: string
  password: string
  full_name?: string
}

const user = ref<User | null>(null)
const token = ref<string | null>(null)

export const useAuth = () => {
  const config = useRuntimeConfig()
  const router = useRouter()

  const apiBase = config.public.apiBaseUrl || 'http://localhost:8000/api/v1'

  const isAuthenticated = computed(() => !!token.value)

  const initAuth = () => {
    if (import.meta.client) {
      const storedToken = localStorage.getItem('auth_token')
      if (storedToken) {
        token.value = storedToken
        fetchCurrentUser()
      }
    }
  }

  const setToken = (newToken: string) => {
    token.value = newToken
    if (import.meta.client) {
      localStorage.setItem('auth_token', newToken)
    }
  }

  const clearToken = () => {
    token.value = null
    user.value = null
    if (import.meta.client) {
      localStorage.removeItem('auth_token')
    }
  }

  const login = async (credentials: LoginCredentials) => {
    try {
      const formData = new URLSearchParams()
      formData.append('username', credentials.username)
      formData.append('password', credentials.password)

      const response = await $fetch<{ access_token: string; token_type: string }>(
        `${apiBase}/auth/login`,
        {
          method: 'POST',
          body: formData,
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
        }
      )

      setToken(response.access_token)
      await fetchCurrentUser()
      return { success: true }
    } catch (error: any) {
      console.error('Login error:', error)
      return {
        success: false,
        error: error.data?.detail || 'Login failed. Please check your credentials.'
      }
    }
  }

  const register = async (data: RegisterData) => {
    try {
      const response = await $fetch<User>(`${apiBase}/auth/register`, {
        method: 'POST',
        body: data,
        headers: {
          'Content-Type': 'application/json',
        },
      })

      return { success: true, user: response }
    } catch (error: any) {
      console.error('Registration error:', error)
      return {
        success: false,
        error: error.data?.detail || 'Registration failed. Please try again.'
      }
    }
  }

  const fetchCurrentUser = async () => {
    if (!token.value) return

    try {
      const response = await $fetch<User>(`${apiBase}/auth/me`, {
        headers: {
          Authorization: `Bearer ${token.value}`,
        },
      })

      user.value = response
    } catch (error) {
      console.error('Failed to fetch current user:', error)
      clearToken()
    }
  }

  const logout = () => {
    clearToken()
    router.push('/login')
  }

  return {
    user,
    token,
    isAuthenticated,
    initAuth,
    login,
    register,
    logout,
    fetchCurrentUser,
  }
}
