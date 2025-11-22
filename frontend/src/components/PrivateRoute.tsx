import { useEffect } from 'react'
import { Navigate, Outlet } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'

export function PrivateRoute() {
  const { isAuthenticated, token, isLoading, loadUser, logout } = useAuthStore()

  useEffect(() => {
    if (token && !isAuthenticated && !isLoading) {
      loadUser().catch(() => {
        logout()
      })
    }
  }, [token, isAuthenticated, isLoading, loadUser, logout])

  if (isLoading) {
    return null
  }

  if (!token || !isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <Outlet />
}
