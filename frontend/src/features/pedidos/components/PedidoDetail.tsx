/**
 * PedidoDetail — vista completa de un pedido.
 *
 * Muestra:
 *   - Dirección (direccion_snapshot)
 *   - Lista de items con snapshots de precio y nombre
 *   - HistorialTimeline
 *   - PaymentStatus (polling en tiempo real)
 *   - CancelarPedidoModal si estado_codigo === "PENDIENTE"
 */

import { useState } from 'react'
import { usePedido } from '../hooks/usePedido'
import { EstadoPedidoBadge } from './EstadoPedidoBadge'
import { HistorialTimeline } from './HistorialTimeline'
import { PaymentStatus } from './PaymentStatus'
import { CancelarPedidoModal } from './CancelarPedidoModal'
import { Button } from '@/components/Button'
import { Skeleton } from '@/components/Skeleton'

interface PedidoDetailProps {
  pedidoId: number
}

function formatFecha(iso: string): string {
  return new Date(iso).toLocaleDateString('es-AR', {
    dateStyle: 'long',
  })
}

function formatMoneda(value: number): string {
  return new Intl.NumberFormat('es-AR', {
    style: 'currency',
    currency: 'ARS',
  }).format(value)
}

export function PedidoDetail({ pedidoId }: PedidoDetailProps) {
  const { data: pedido, isLoading, isError } = usePedido(pedidoId)
  const [showCancelarModal, setShowCancelarModal] = useState(false)

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-32 w-full" />
      </div>
    )
  }

  if (isError || !pedido) {
    return (
      <p className="text-error text-sm">
        No se pudo cargar el pedido. Intentá nuevamente.
      </p>
    )
  }

  const dir = pedido.direccion_snapshot as Record<string, unknown>

  return (
    <div className="space-y-6">
      {/* Encabezado */}
      <div className="flex items-start justify-between flex-wrap gap-3">
        <div>
          <p className="text-sm text-text-secondary">Pedido #{pedido.id}</p>
          <p className="text-sm text-text-secondary">{formatFecha(pedido.created_at)}</p>
        </div>
        <div className="flex items-center gap-3">
          <EstadoPedidoBadge estado={pedido.estado_codigo} />
          <PaymentStatus pedidoId={pedido.id} />
        </div>
      </div>

      {/* Total */}
      <div className="bg-surface rounded-md p-4">
        <p className="text-sm text-text-secondary">Total del pedido</p>
        <p className="text-2xl font-semibold text-text-primary">
          {formatMoneda(pedido.total)}
        </p>
      </div>

      {/* Dirección */}
      <section>
        <h2 className="text-base font-semibold text-text-primary mb-2">Dirección de entrega</h2>
        <div className="bg-surface rounded-md p-4 text-sm text-text-secondary space-y-1">
          <p>
            {String(dir.calle ?? '')} {String(dir.numero ?? '')}
            {dir.piso ? `, piso ${String(dir.piso)}` : ''}
            {dir.depto ? ` depto ${String(dir.depto)}` : ''}
          </p>
          <p>
            {String(dir.ciudad ?? '')}, {String(dir.provincia ?? '')} — CP {String(dir.codigo_postal ?? '')}
          </p>
          {dir.referencia && (
            <p className="italic">Referencia: {String(dir.referencia)}</p>
          )}
        </div>
      </section>

      {/* Items */}
      <section>
        <h2 className="text-base font-semibold text-text-primary mb-2">Productos</h2>
        <ul className="divide-y divide-border-color border border-border-color rounded-md overflow-hidden">
          {pedido.items.map((item) => (
            <li key={item.id} className="flex items-center justify-between px-4 py-3 bg-white">
              <div>
                <p className="text-sm font-medium text-text-primary">{item.nombre_snapshot}</p>
                <p className="text-xs text-text-secondary">
                  {formatMoneda(item.precio_snapshot)} × {item.cantidad}
                </p>
              </div>
              <p className="text-sm font-semibold text-text-primary">
                {formatMoneda(item.precio_snapshot * item.cantidad)}
              </p>
            </li>
          ))}
        </ul>
      </section>

      {/* Historial */}
      <section>
        <h2 className="text-base font-semibold text-text-primary mb-3">Historial de estados</h2>
        <HistorialTimeline historial={pedido.historial} />
      </section>

      {/* Cancelar pedido (solo si PENDIENTE) */}
      {pedido.estado_codigo === 'PENDIENTE' && (
        <div className="pt-2">
          <Button
            variant="secondary"
            onClick={() => setShowCancelarModal(true)}
            className="text-red-600 border-red-300 hover:bg-red-50"
          >
            Cancelar pedido
          </Button>

          <CancelarPedidoModal
            open={showCancelarModal}
            onClose={() => setShowCancelarModal(false)}
            pedidoId={pedido.id}
          />
        </div>
      )}
    </div>
  )
}
