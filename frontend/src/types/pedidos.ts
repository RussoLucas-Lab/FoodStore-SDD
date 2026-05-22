import type { PagoRead } from './pagos'

export interface PedidoRead {
  id: number
  estado_codigo: string
  total: number
  created_at: string
}

export interface DetallePedidoRead {
  id: number
  producto_id: number
  nombre_snapshot: string
  precio_snapshot: number
  cantidad: number
  personalizacion: number[] | null
}

export interface HistorialEstadoRead {
  id: number
  estado_desde: string | null
  estado_hasta: string
  cambiado_por_id: number | null
  motivo: string | null
  created_at: string
}

export interface PedidoDetailRead extends PedidoRead {
  direccion_snapshot: Record<string, unknown>
  items: DetallePedidoRead[]
  historial: HistorialEstadoRead[]
  pago: PagoRead | null
}

export interface PedidoListResponse {
  items: PedidoRead[]
  total: number
  page: number
  size: number
  pages: number
}

/** @deprecated Use PedidoDetailRead instead */
export interface PedidoDetail extends PedidoRead {
  subtotal: number
  costo_envio: number
  direccion_snapshot: Record<string, unknown>
  items: DetallePedidoRead[]
}

export interface ItemPedidoCreate {
  producto_id: number
  cantidad: number
  personalizacion?: number[]
  precio_esperado?: number
}

export interface PedidoCreate {
  direccion_id: number
  forma_pago_codigo: string
  items: ItemPedidoCreate[]
  notas?: string
}
