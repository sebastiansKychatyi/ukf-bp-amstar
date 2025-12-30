/**
 * User roles in the AmStar system
 */
export enum UserRole {
  PLAYER = 'PLAYER',
  CAPTAIN = 'CAPTAIN',
  REFEREE = 'REFEREE'
}

/**
 * User interface with role information
 */
export interface User {
  id: number
  email: string
  username: string
  full_name?: string
  role: UserRole
  is_active: boolean
  is_superuser: boolean
  created_at: string
  updated_at: string
}

/**
 * Login credentials
 */
export interface LoginCredentials {
  username: string
  password: string
}

/**
 * Registration data
 */
export interface RegisterData {
  email: string
  username: string
  password: string
  full_name?: string
  role?: UserRole
}

/**
 * Auth token response
 */
export interface TokenResponse {
  access_token: string
  token_type: string
}
