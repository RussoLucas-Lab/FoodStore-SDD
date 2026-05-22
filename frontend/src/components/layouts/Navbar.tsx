import { Link } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { useLogout } from '@/features/auth/hooks/useLogout'
import { CartBadge } from '@/features/carrito/components/CartBadge'

export function Navbar() {
  const usuario = useAuthStore((s) => s.usuario)
  const accessToken = useAuthStore((s) => s.accessToken)
  const logoutMutation = useLogout()

  return (
    <nav className="sticky top-0 z-40 w-full backdrop-blur bg-white/80 border-b border-border-color">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between">
        <Link
          to="/"
          className="text-lg font-semibold text-text-primary tracking-tight"
        >
          Food Store
        </Link>

        <div className="flex items-center gap-3 text-sm">
          <Link to="/catalogo" className="text-text-secondary hover:text-text-primary transition-colors">
            Catálogo
          </Link>

          {accessToken && usuario?.rol === 'CLIENT' && (
            <Link
              to="/pedidos"
              className="text-text-secondary hover:text-text-primary transition-colors"
            >
              Mis pedidos
            </Link>
          )}

          {/* Badge del carrito — visible para todos */}
          <CartBadge />

          {accessToken && usuario ? (
            <div className="flex items-center gap-3">
              <Link
                to="/perfil"
                className="text-text-secondary hover:text-text-primary transition-colors"
              >
                Mi Perfil
              </Link>
              <span className="text-text-secondary hidden sm:block">
                {usuario.nombre}
              </span>
              <button
                onClick={() => void logoutMutation.mutate()}
                disabled={logoutMutation.isPending}
                className="text-text-secondary hover:text-error transition-colors"
              >
                Salir
              </button>
            </div>
          ) : (
            <Link
              to="/login"
              className="bg-blue text-white px-4 py-1.5 rounded-full text-sm font-medium hover:bg-blue-dark transition-colors"
            >
              Iniciar sesión
            </Link>
          )}
        </div>
      </div>
    </nav>
  )
}
