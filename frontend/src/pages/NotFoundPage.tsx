/** NotFoundPage — página 404. */
import { Link } from 'react-router-dom'

export default function NotFoundPage() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center gap-4 px-4">
      <h1 className="text-6xl font-bold text-text-primary">404</h1>
      <p className="text-xl text-text-secondary">Página no encontrada</p>
      <Link
        to="/"
        className="mt-4 px-6 py-2.5 bg-blue text-white rounded-full text-sm font-medium hover:bg-blue-dark transition-colors"
      >
        Volver al inicio
      </Link>
    </main>
  )
}
