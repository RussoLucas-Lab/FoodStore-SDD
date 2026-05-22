/** PedidosPage — historial de pedidos del usuario autenticado. */
import { PedidosList } from '@/features/pedidos/components/PedidosList'

export default function PedidosPage() {
  return (
    <main className="max-w-product mx-auto px-4 py-10">
      <h1 className="text-2xl font-semibold text-text-primary mb-6">
        Mis Pedidos
      </h1>
      <PedidosList />
    </main>
  )
}
