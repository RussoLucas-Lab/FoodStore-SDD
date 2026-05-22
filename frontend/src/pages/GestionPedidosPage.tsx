/**
 * GestionPedidosPage — panel de gestión de pedidos para roles ADMIN y PEDIDOS.
 *
 * Protegida vía ProtectedRoute — solo accesible por ADMIN y PEDIDOS.
 */

import { GestionPedidosTable } from '@/features/admin/components/GestionPedidosTable'

export default function GestionPedidosPage() {
  return (
    <main className="max-w-grid mx-auto px-4 py-10">
      <h1 className="text-2xl font-semibold text-text-primary mb-6">
        Gestión de Pedidos
      </h1>
      <GestionPedidosTable />
    </main>
  )
}
