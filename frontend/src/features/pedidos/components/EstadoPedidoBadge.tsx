/**
 * EstadoPedidoBadge — badge con color semántico por estado de pedido.
 *
 * Colores por estado (design system):
 *   PENDIENTE   → amarillo
 *   CONFIRMADO  → azul
 *   EN_PREP     → naranja
 *   EN_CAMINO   → violeta
 *   ENTREGADO   → verde
 *   CANCELADO   → rojo
 */

interface EstadoPedidoBadgeProps {
  estado: string
  className?: string
}

const ESTADO_STYLES: Record<string, string> = {
  PENDIENTE: 'bg-yellow-100 text-yellow-800',
  CONFIRMADO: 'bg-blue-100 text-blue-800',
  EN_PREP: 'bg-orange-100 text-orange-800',
  EN_CAMINO: 'bg-purple-100 text-purple-800',
  ENTREGADO: 'bg-green-100 text-green-800',
  CANCELADO: 'bg-red-100 text-red-800',
}

const ESTADO_LABELS: Record<string, string> = {
  PENDIENTE: 'Pendiente',
  CONFIRMADO: 'Confirmado',
  EN_PREP: 'En preparación',
  EN_CAMINO: 'En camino',
  ENTREGADO: 'Entregado',
  CANCELADO: 'Cancelado',
}

export function EstadoPedidoBadge({ estado, className = '' }: EstadoPedidoBadgeProps) {
  const styles = ESTADO_STYLES[estado] ?? 'bg-gray-100 text-gray-700'
  const label = ESTADO_LABELS[estado] ?? estado

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${styles} ${className}`}
    >
      {label}
    </span>
  )
}
