import { useQuery } from '@tanstack/react-query'
import { getPedidosPorEstado } from '@/api/endpoints/admin'
import type { PedidosPorEstadoResponse } from '@/types/admin'

export function usePedidosPorEstado() {
  return useQuery<PedidosPorEstadoResponse>({
    queryKey: ['admin', 'metricas', 'pedidos-por-estado'],
    queryFn: getPedidosPorEstado,
    staleTime: 5 * 60 * 1000,
  })
}
