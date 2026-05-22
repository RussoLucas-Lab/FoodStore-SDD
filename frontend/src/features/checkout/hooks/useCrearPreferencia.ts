import { useMutation } from '@tanstack/react-query'
import { crearPreferencia } from '@/api/endpoints/pagos'
import type { CrearPagoResponse } from '@/types/pagos'
import type { AxiosError } from 'axios'

interface ErrorBody {
  detail?: string
}

/**
 * Hook para crear una preferencia de pago en MercadoPago.
 * Llama POST /api/v1/pagos/crear con el pedidoId.
 */
export function useCrearPreferencia() {
  return useMutation<CrearPagoResponse, AxiosError<ErrorBody>, number>({
    mutationFn: (pedidoId: number) => crearPreferencia({ pedido_id: pedidoId }),
  })
}
