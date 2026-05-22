import { Navigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import type { Rol } from '@/types/auth'

interface ProtectedRouteProps {
  children: React.ReactNode
  roles?: Rol[]
}

export function ProtectedRoute({ children, roles }: ProtectedRouteProps) {
  const accessToken = useAuthStore((s) => s.accessToken)
  const usuario = useAuthStore((s) => s.usuario)
  const location = useLocation()

  if (!accessToken) {
    return (
      <Navigate
        to={`/login?next=${encodeURIComponent(location.pathname)}`}
        replace
      />
    )
  }

  if (roles && roles.length > 0 && usuario) {
    const hasRequiredRole = roles.includes(usuario.rol)
    if (!hasRequiredRole) {
      return <Navigate to="/" replace />
    }
  }

  return <>{children}</>
}
