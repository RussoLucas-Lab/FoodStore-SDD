/**
 * useGestionPedidos — hook para el panel de gestión de pedidos (admin).
 *
 * El backend filtra por rol automáticamente:
 *   - ADMIN / PEDIDOS → ve todos los pedidos.
 *   - CLIENT → solo sus propios (pero este hook es solo para admin).
 *
 * Query key: ['pedidos', params] — compatible con el listado del cliente
 * para aprovechar la caché compartida.
 */

import { useQuery } from '@tanstack/react-query'
import { getPedidos, type GetPedidosParams } from '@/api/endpoints/pedidos'
import type { PedidoListResponse } from '@/types/pedidos'

export function useGestionPedidos(params?: GetPedidosParams) {
  return useQuery<PedidoListResponse>({
    queryKey: ['pedidos', params ?? {}],
    queryFn: () => getPedidos(params),
  })
}
