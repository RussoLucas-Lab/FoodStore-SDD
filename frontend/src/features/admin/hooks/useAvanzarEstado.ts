/**
 * useAvanzarEstado — mutation para avanzar el estado de un pedido via FSM.
 *
 * Usa PATCH /api/v1/pedidos/{id}/estado.
 * Al completarse con éxito, invalida ['pedidos'] para refrescar la tabla.
 */

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/api/client'

interface AvanzarEstadoParams {
  pedidoId: number
  nuevo_estado: string
  motivo?: string
}

interface CambiarEstadoResponse {
  id: number
  estado_codigo: string
  estado_anterior: string
  total: number
  created_at: string
}

export function useAvanzarEstado() {
  const queryClient = useQueryClient()

  return useMutation<CambiarEstadoResponse, Error, AvanzarEstadoParams>({
    mutationFn: async ({ pedidoId, nuevo_estado, motivo }) => {
      const response = await apiClient.patch<CambiarEstadoResponse>(
        `/api/v1/pedidos/${pedidoId}/estado`,
        { nuevo_estado, motivo },
      )
      return response.data
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['pedidos'] })
    },
  })
}
