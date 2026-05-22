/** Tipos TypeScript para el módulo de pagos. */

export interface CrearPagoRequest {
  pedido_id: number
}

export interface CrearPagoResponse {
  preference_id: string
  init_point: string
}

export interface PagoRead {
  id: number
  pedido_id: number
  estado_pago: string
  mp_payment_id: string | null
  mp_preference_id: string | null
  created_at: string
}
