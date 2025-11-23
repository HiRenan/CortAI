/**
 * Authentication service
 */
import api from '../lib/axios'
import type { LoginRequest, RegisterRequest, TokenResponse, User } from '../types/api'

export const authService = {
  /**
   * Register a new user
   */
  async register(data: RegisterRequest): Promise<User> {
    const response = await api.post<User>('/api/v1/auth/register', data)
    return response.data
  },

  /**
   * Login user and get access token
   */
  async login(data: LoginRequest): Promise<TokenResponse> {
    // OAuth2 password flow requires form-urlencoded
    const formData = new URLSearchParams()
    formData.append('username', data.username)
    formData.append('password', data.password)

    const response = await api.post<TokenResponse>('/api/v1/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    })

    return response.data
  },

  /**
   * Get current authenticated user
   */
  async getCurrentUser(): Promise<User> {
    const response = await api.get<User>('/api/v1/auth/me')
    return response.data
  },

  /**
   * Logout user (clear token from storage)
   */
  logout(): void {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('auth-storage')
  },
}

export default authService
