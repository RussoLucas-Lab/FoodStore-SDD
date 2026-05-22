/**
 * PedidoDetailPage — página de detalle de un pedido.
 *
 * Extrae el parámetro :id de la URL, renderiza PedidoDetail.
 * Si el pedido no existe (404), redirige a /pedidos con un toast de error.
 */

import { useParams, useNavigate } from 'react-router-dom'
import { useEffect } from 'react'
import { PedidoDetail } from '@/features/pedidos/components/PedidoDetail'
import { usePedido } from '@/features/pedidos/hooks/usePedido'
import { useUiStore } from '@/store/uiStore'
import { Link } from 'react-router-dom'

export default function PedidoDetailPage() {
  const { id } = useParams<{ id: string }>()
  const pedidoId = id ? parseInt(id, 10) : undefined
  const navigate = useNavigate()
  const addToast = useUiStore((s) => s.addToast)

  const { isError, error } = usePedido(pedidoId)

  useEffect(() => {
    if (isError) {
      const status =
        (error as { response?: { status?: number } }).response?.status
      if (status === 404) {
        addToast('Pedido no encontrado.', 'error')
        void navigate('/pedidos', { replace: true })
      }
    }
  }, [isError, error, navigate, addToast])

  if (!pedidoId || isNaN(pedidoId)) {
    return (
      <main className="max-w-product mx-auto px-4 py-10">
        <p className="text-error text-sm">ID de pedido inválido.</p>
      </main>
    )
  }

  return (
    <main className="max-w-product mx-auto px-4 py-10">
      <Link
        to="/pedidos"
        className="inline-flex items-center gap-1 text-sm text-blue hover:underline mb-6"
      >
        ← Volver a mis pedidos
      </Link>

      <h1 className="text-2xl font-semibold text-text-primary mb-6">
        Detalle del pedido
      </h1>

      <PedidoDetail pedidoId={pedidoId} />
    </main>
  )
}
