import { useEffect } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { LoginForm } from '@/features/auth/components/LoginForm'
import { useAuthStore } from '@/store/authStore'

export default function LoginPage() {
  const accessToken = useAuthStore((s) => s.accessToken)
  const usuario = useAuthStore((s) => s.usuario)
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  useEffect(() => {
    if (accessToken) {
      const next = searchParams.get('next')
      if (next) {
        // Redirigir a la ruta solicitada originalmente (e.g. ?next=/admin)
        navigate(next, { replace: true })
      } else if (usuario) {
        // Redirigir según el rol del usuario
        const adminRoles = ['ADMIN', 'STOCK', 'PEDIDOS']
        const target = adminRoles.includes(usuario.rol) ? '/admin' : '/'
        navigate(target, { replace: true })
      }
      // Si accessToken existe pero usuario aún no cargó, esperamos al próximo render
    }
  }, [accessToken, usuario, navigate, searchParams])

  return (
    <main className="min-h-screen flex items-center justify-center bg-surface px-4">
      <div className="w-full max-w-sm">
        <h1 className="text-2xl font-semibold text-text-primary mb-2 text-center">
          Iniciar sesión
        </h1>
        <p className="text-text-secondary text-sm text-center mb-8">
          Ingresá con tu cuenta de Food Store.
        </p>

        <LoginForm />

        <p className="mt-6 text-center text-sm text-text-secondary">
          ¿No tenés cuenta?{' '}
          <Link to="/register" className="text-blue hover:underline">
            Registrate
          </Link>
        </p>
      </div>
    </main>
  )
}
