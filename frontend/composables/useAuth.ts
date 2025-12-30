import { ref, computed } from 'vue'
import type { User, LoginCredentials, RegisterData, TokenResponse, UserRole } from '@/types/auth'

const user = ref<User | null>(null)

export const useAuth = () => {
  const config = useRuntimeConfig()
  const router = useRouter()

  // Use useCookie for SSR compatibility
  const token = useCookie<string | null>('auth_token', {
    maxAge: 60 * 60 * 24 * 7, // 7 days
    sameSite: 'lax',
    secure: process.env.NODE_ENV === 'production',
  })

  const apiBase = config.public.apiBaseUrl || 'http://localhost:8000/api/v1'

  const isAuthenticated = computed(() => !!token.value)

  // Role-based computed properties
  const isPlayer = computed(() => user.value?.role === 'PLAYER')
  const isCaptain = computed(() => user.value?.role === 'CAPTAIN')
  const isReferee = computed(() => user.value?.role === 'REFEREE')

  const initAuth = async () => {
    if (token.value) {
      await fetchCurrentUser()
    }
  }

  const setToken = (newToken: string) => {
    token.value = newToken
  }

  const clearToken = () => {
    token.value = null
    user.value = null
  }

  const login = async (credentials: LoginCredentials) => {
    try {
      const formData = new URLSearchParams()
      formData.append('username', credentials.username)
      formData.append('password', credentials.password)

      const response = await $fetch<TokenResponse>(
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

  const logout = async () => {
    // Call backend logout endpoint to blacklist token
    if (token.value) {
      try {
        await $fetch(`${apiBase}/auth/logout`, {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${token.value}`,
          },
        })
      } catch (error) {
        console.error('Logout API call failed:', error)
      }
    }

    clearToken()
    router.push('/auth/login')
  }

  return {
    user,
    token,
    isAuthenticated,
    isPlayer,
    isCaptain,
    isReferee,
    initAuth,
    login,
    register,
    logout,
    fetchCurrentUser,
  }
}
