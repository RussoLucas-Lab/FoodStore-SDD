/**
 * usePedidos — hook para listar pedidos del usuario autenticado.
 *
 * Usa TanStack Query con query key ['pedidos', params] para cache independiente
 * por combinación de parámetros de filtro y paginación.
 */

import { useQuery } from '@tanstack/react-query'
import { getPedidos, type GetPedidosParams } from '@/api/endpoints/pedidos'
import type { PedidoListResponse } from '@/types/pedidos'

export function usePedidos(params?: GetPedidosParams) {
  return useQuery<PedidoListResponse>({
    queryKey: ['pedidos', params ?? {}],
    queryFn: () => getPedidos(params),
  })
}
