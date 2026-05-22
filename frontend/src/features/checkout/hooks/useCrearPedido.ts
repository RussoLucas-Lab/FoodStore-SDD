import { useMutation } from '@tanstack/react-query'
import { crearPedido } from '@/api/endpoints/pedidos'
import { useUiStore } from '@/store/uiStore'
import type { PedidoCreate, PedidoRead } from '@/types/pedidos'
import type { AxiosError } from 'axios'

interface ErrorBody {
  detail?: string
}

/**
 * Hook para crear un pedido.
 *
 * El caller puede pasar onSuccess en mutate() para controlar la navegación.
 * El hook solo maneja el caso de error genérico con un toast.
 */
export function useCrearPedido(idempotencyKey: string) {
  return useMutation<PedidoRead, AxiosError<ErrorBody>, PedidoCreate>({
    mutationFn: (body: PedidoCreate) => crearPedido(body, idempotencyKey),
    onError: (error: AxiosError<ErrorBody>) => {
      const detail = error.response?.data?.detail ?? 'Error al crear el pedido'
      useUiStore.getState().addToast(String(detail), 'error')
    },
  })
}
