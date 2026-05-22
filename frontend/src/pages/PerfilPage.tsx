import { PerfilForm } from '@/features/auth/components/PerfilForm'
import { CambiarPasswordForm } from '@/features/auth/components/CambiarPasswordForm'

export default function PerfilPage() {
  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-2xl font-bold text-text-primary mb-8">Mi perfil</h1>

      {/* Datos personales */}
      <section className="bg-surface rounded-md shadow-card p-6 mb-6">
        <h2 className="text-lg font-semibold text-text-primary mb-4">
          Mis datos
        </h2>
        <PerfilForm />
      </section>

      {/* Cambiar contraseña */}
      <section className="bg-surface rounded-md shadow-card p-6">
        <h2 className="text-lg font-semibold text-text-primary mb-4">
          Cambiar contraseña
        </h2>
        <CambiarPasswordForm />
      </section>
    </div>
  )
}
