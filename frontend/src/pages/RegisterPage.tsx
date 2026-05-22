import { useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { RegisterForm } from '@/features/auth/components/RegisterForm'
import { useAuthStore } from '@/store/authStore'

export default function RegisterPage() {
  const accessToken = useAuthStore((s) => s.accessToken)
  const navigate = useNavigate()

  useEffect(() => {
    if (accessToken) {
      navigate('/', { replace: true })
    }
  }, [accessToken, navigate])

  return (
    <main className="min-h-screen flex items-center justify-center bg-surface px-4">
      <div className="w-full max-w-sm">
        <h1 className="text-2xl font-semibold text-text-primary mb-2 text-center">
          Crear cuenta
        </h1>
        <p className="text-text-secondary text-sm text-center mb-8">
          Completá tus datos para registrarte.
        </p>

        <RegisterForm />

        <p className="mt-6 text-center text-sm text-text-secondary">
          ¿Ya tenés cuenta?{' '}
          <Link to="/login" className="text-blue hover:underline">
            Iniciá sesión
          </Link>
        </p>
      </div>
    </main>
  )
}
