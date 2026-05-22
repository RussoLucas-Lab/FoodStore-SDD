import { apiClient } from '@/api/client'
import type { FormaPagoRead } from '@/types/formasPago'

export async function listFormasPago(): Promise<FormaPagoRead[]> {
  const response = await apiClient.get<FormaPagoRead[]>('/api/v1/pedidos/formas-pago')
  return response.data
}
