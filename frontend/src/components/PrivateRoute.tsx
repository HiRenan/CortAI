import { useEffect } from 'react'
import { Navigate, Outlet } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'

export function PrivateRoute() {
  const { isAuthenticated, token, loadUser } = useAuthStore()

  useEffect(() => {
    // If we have a token but no user data, load user
    if (token && !isAuthenticated) {
      loadUser().catch(() => {
        // If loading user fails, will redirect to login
      })
    }
  }, [token, isAuthenticated, loadUser])

  // If no token, redirect to login
  if (!token) {
    return <Navigate to="/login" replace />
  }

  // If we have token but still loading user, show nothing (could add a loading spinner)
  if (token && !isAuthenticated) {
    return null
  }

  // User is authenticated, render children routes
  return <Outlet />
}
