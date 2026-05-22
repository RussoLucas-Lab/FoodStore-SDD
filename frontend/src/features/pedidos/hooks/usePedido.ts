/**
 * usePedido — hook para obtener el detalle completo de un pedido por ID.
 *
 * Query key: ['pedido', id]
 * Incluye items con snapshots, historial de estados y estado de pago.
 */

import { useQuery } from '@tanstack/react-query'
import { getPedidoById } from '@/api/endpoints/pedidos'
import type { PedidoDetailRead } from '@/types/pedidos'

export function usePedido(id: number | undefined) {
  return useQuery<PedidoDetailRead>({
    queryKey: ['pedido', id],
    queryFn: () => getPedidoById(id!),
    enabled: id !== undefined,
  })
}
