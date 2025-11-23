/**
 * Authentication store with Zustand and persist middleware
 */
import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import authService from '../services/authService'
import type { User, LoginRequest, RegisterRequest } from '../types/api'

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
}

interface AuthActions {
  login: (credentials: LoginRequest) => Promise<void>
  register: (data: RegisterRequest) => Promise<void>
  logout: () => void
  loadUser: () => Promise<void>
  setUser: (user: User | null) => void
  setToken: (token: string | null) => void
  setError: (error: string | null) => void
  clearError: () => void
}

type AuthStore = AuthState & AuthActions

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      // State
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      // Actions
      login: async (credentials: LoginRequest) => {
        try {
          set({ isLoading: true, error: null })

          const tokenResponse = await authService.login(credentials)

          // Save token to localStorage and state
          localStorage.setItem('auth_token', tokenResponse.access_token)
          set({ token: tokenResponse.access_token })

          // Load user data
          await get().loadUser()
        } catch (error: unknown) {
          const errorMessage = error instanceof Error ? error.message : 'Falha no login'
          set({ error: errorMessage, isLoading: false })
          throw error
        }
      },

      register: async (data: RegisterRequest) => {
        try {
          set({ isLoading: true, error: null })

          await authService.register(data)

          // After registration, login automatically
          await get().login({
            username: data.email,
            password: data.password,
          })
        } catch (error: unknown) {
          const errorMessage = error instanceof Error ? error.message : 'Falha no registro'
          set({ error: errorMessage, isLoading: false })
          throw error
        }
      },

      logout: () => {
        authService.logout()
        set({
          user: null,
          token: null,
          isAuthenticated: false,
          error: null,
        })
      },

      loadUser: async () => {
        try {
          set({ isLoading: true, error: null })

          const user = await authService.getCurrentUser()

          set({
            user,
            isAuthenticated: true,
            isLoading: false,
          })
        } catch (error: unknown) {
          const errorMessage = error instanceof Error ? error.message : 'Falha ao carregar usuário'
          set({
            user: null,
            isAuthenticated: false,
            error: errorMessage,
            isLoading: false,
          })
          throw error
        }
      },

      setUser: (user: User | null) => {
        set({
          user,
          isAuthenticated: !!user,
        })
      },

      setToken: (token: string | null) => {
        if (token) {
          localStorage.setItem('auth_token', token)
        } else {
          localStorage.removeItem('auth_token')
        }
        set({ token })
      },

      setError: (error: string | null) => {
        set({ error })
      },

      clearError: () => {
        set({ error: null })
      },
    }),
    {
      name: 'auth-storage', // localStorage key
      storage: createJSONStorage(() => localStorage),
      // Only persist user and token, not loading/error states
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)

export default useAuthStore
