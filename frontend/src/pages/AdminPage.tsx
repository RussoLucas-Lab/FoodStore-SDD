/** AdminPage — panel de administración (requiere rol ADMIN). */
export default function AdminPage() {
  return (
    <main className="max-w-grid mx-auto px-4 py-10">
      <h1 className="text-2xl font-semibold text-text-primary mb-6">
        Panel de Administración
      </h1>
      <p className="text-text-secondary">
        Próximamente: dashboard con gráficos, CRUD de productos y gestión de pedidos.
      </p>
    </main>
  )
}
