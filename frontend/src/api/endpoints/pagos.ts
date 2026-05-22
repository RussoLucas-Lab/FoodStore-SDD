import { apiClient } from '@/api/client'
import type { CrearPagoRequest, CrearPagoResponse, PagoRead } from '@/types/pagos'

export async function crearPreferencia(body: CrearPagoRequest): Promise<CrearPagoResponse> {
  const response = await apiClient.post<CrearPagoResponse>('/api/v1/pagos/crear', body)
  return response.data
}

export async function getPagoPorPedido(pedidoId: number): Promise<PagoRead> {
  const response = await apiClient.get<PagoRead>(`/api/v1/pagos/${pedidoId}`)
  return response.data
}
