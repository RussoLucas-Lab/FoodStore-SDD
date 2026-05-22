/**
 * PedidoCard — tarjeta de resumen de un pedido en el listado.
 *
 * Muestra: id, fecha formateada, EstadoPedidoBadge, total, enlace a /pedidos/:id
 */

import { Link } from 'react-router-dom'
import type { PedidoRead } from '@/types/pedidos'
import { EstadoPedidoBadge } from './EstadoPedidoBadge'

interface PedidoCardProps {
  pedido: PedidoRead
}

function formatFecha(iso: string): string {
  return new Date(iso).toLocaleDateString('es-AR', { dateStyle: 'medium' })
}

function formatMoneda(value: number): string {
  return new Intl.NumberFormat('es-AR', {
    style: 'currency',
    currency: 'ARS',
  }).format(value)
}

export function PedidoCard({ pedido }: PedidoCardProps) {
  return (
    <Link
      to={`/pedidos/${pedido.id}`}
      className="block bg-white border border-border-color rounded-md p-4 hover:shadow-md transition-shadow"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-sm font-medium text-text-primary truncate">
            Pedido #{pedido.id}
          </p>
          <p className="text-xs text-text-secondary mt-0.5">
            {formatFecha(pedido.created_at)}
          </p>
        </div>
        <EstadoPedidoBadge estado={pedido.estado_codigo} />
      </div>

      <div className="mt-3 flex items-center justify-between">
        <p className="text-base font-semibold text-text-primary">
          {formatMoneda(pedido.total)}
        </p>
        <span className="text-xs text-blue hover:underline">Ver detalle →</span>
      </div>
    </Link>
  )
}
