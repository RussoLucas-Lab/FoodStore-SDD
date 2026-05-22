/**
 * useCancelarPedido — mutation para cancelar un pedido propio (DELETE /pedidos/{id}).
 *
 * Al completarse con éxito:
 *   - invalida ['pedidos'] para refrescar el listado
 *   - invalida ['pedido', id] para refrescar el detalle
 */

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { cancelarPedido } from '@/api/endpoints/pedidos'

interface CancelarParams {
  id: number
  motivo: string
}

export function useCancelarPedido() {
  const queryClient = useQueryClient()

  return useMutation<void, Error, CancelarParams>({
    mutationFn: ({ id, motivo }) => cancelarPedido(id, motivo),
    onSuccess: (_data, variables) => {
      void queryClient.invalidateQueries({ queryKey: ['pedidos'] })
      void queryClient.invalidateQueries({ queryKey: ['pedido', variables.id] })
    },
  })
}
