import { apiClient } from '@/api/client'
import type {
  HistorialEstadoRead,
  PedidoCreate,
  PedidoDetailRead,
  PedidoListResponse,
  PedidoRead,
} from '@/types/pedidos'

export interface GetPedidosParams {
  estado_codigo?: string
  page?: number
  size?: number
}

export async function crearPedido(body: PedidoCreate, idempotencyKey: string): Promise<PedidoRead> {
  const response = await apiClient.post<PedidoRead>('/api/v1/pedidos', body, {
    headers: { 'Idempotency-Key': idempotencyKey },
  })
  return response.data
}

export async function getPedidos(params?: GetPedidosParams): Promise<PedidoListResponse> {
  const response = await apiClient.get<PedidoListResponse>('/api/v1/pedidos', { params })
  return response.data
}

export async function getPedidoById(id: number): Promise<PedidoDetailRead> {
  const response = await apiClient.get<PedidoDetailRead>(`/api/v1/pedidos/${id}`)
  return response.data
}

export async function getPedidoHistorial(id: number): Promise<HistorialEstadoRead[]> {
  const response = await apiClient.get<HistorialEstadoRead[]>(`/api/v1/pedidos/${id}/historial`)
  return response.data
}

export async function cancelarPedido(id: number, motivo: string): Promise<void> {
  await apiClient.delete(`/api/v1/pedidos/${id}`, { data: { motivo } })
}
