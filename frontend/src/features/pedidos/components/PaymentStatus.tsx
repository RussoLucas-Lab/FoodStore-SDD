/**
 * PaymentStatus — badge del estado actual del pago de un pedido.
 *
 * Hace polling cada 30 segundos mientras el estado NO es terminal.
 * Estados terminales: APROBADO, RECHAZADO, ERROR (desactivan el polling).
 *
 * Usa TanStack Query para gestión del estado del servidor.
 */

import { useQuery } from '@tanstack/react-query'
import { getPagoPorPedido } from '@/api/endpoints/pagos'

interface PaymentStatusProps {
  pedidoId: number
}

const TERMINAL_STATES = new Set(['APROBADO', 'RECHAZADO', 'ERROR'])

const ESTADO_STYLES: Record<string, string> = {
  APROBADO: 'bg-green-100 text-green-800',
  RECHAZADO: 'bg-red-100 text-red-800',
  ERROR: 'bg-red-100 text-red-800',
  PENDIENTE: 'bg-yellow-100 text-yellow-800',
  EN_PROCESO: 'bg-blue-100 text-blue-800',
}

const ESTADO_LABELS: Record<string, string> = {
  APROBADO: 'Pago aprobado',
  RECHAZADO: 'Pago rechazado',
  ERROR: 'Error en el pago',
  PENDIENTE: 'Pago pendiente',
  EN_PROCESO: 'Procesando pago',
}

export function PaymentStatus({ pedidoId }: PaymentStatusProps) {
  const { data: pago, isLoading } = useQuery({
    queryKey: ['pago', pedidoId],
    queryFn: () => getPagoPorPedido(pedidoId),
    refetchInterval: (query) => {
      const estado = query.state.data?.estado_pago
      if (!estado || TERMINAL_STATES.has(estado)) return false
      return 30_000
    },
    retry: false,
  })

  if (isLoading) {
    return (
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
        Verificando pago...
      </span>
    )
  }

  if (!pago) {
    return (
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
        Sin registro de pago
      </span>
    )
  }

  const styles = ESTADO_STYLES[pago.estado_pago] ?? 'bg-gray-100 text-gray-700'
  const label = ESTADO_LABELS[pago.estado_pago] ?? pago.estado_pago

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${styles}`}
      role="status"
      aria-label={`Estado de pago: ${label}`}
    >
      {label}
    </span>
  )
}
