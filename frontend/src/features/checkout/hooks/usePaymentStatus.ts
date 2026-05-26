import { useEffect } from 'react'
import type { AxiosError } from 'axios'
import { getPagoPorPedido } from '@/api/endpoints/pagos'
import { usePaymentStore } from '@/store/paymentStore'

const POLLING_INTERVAL_MS = 30_000 // 30 segundos

/**
 * Hook que hace polling del estado de pago cada 30 segundos (US-072).
 *
 * Solo activo cuando:
 *   - pedidoId no es null
 *   - paymentStore.status === 'processing'
 *
 * Se detiene cuando el status pasa a 'approved', 'rejected' o 'error',
 * o cuando el componente se desmonta (cleanup del interval).
 */
export function usePaymentStatus(pedidoId: number | null): void {
  const status = usePaymentStore((s) => s.status)
  const setApproved = usePaymentStore((s) => s.setApproved)
  const setRejected = usePaymentStore((s) => s.setRejected)
  const setError = usePaymentStore((s) => s.setError)

  useEffect(() => {
    if (pedidoId === null || status !== 'processing') return

    const checkStatus = async () => {
      try {
        const pago = await getPagoPorPedido(pedidoId)
        if (pago.estado_pago === 'APROBADO') {
          setApproved()
        } else if (pago.estado_pago === 'RECHAZADO') {
          setRejected()
        }
      } catch (err) {
        const axiosErr = err as AxiosError
        // 404 = pago aún no registrado, seguir esperando sin marcar error
        if (axiosErr.response?.status !== 404) {
          setError('Error al verificar el estado del pago')
        }
      }
    }

    // Llamada inmediata + polling
    checkStatus()
    const intervalId = setInterval(checkStatus, POLLING_INTERVAL_MS)

    return () => {
      clearInterval(intervalId)
    }
  }, [pedidoId, status, setApproved, setRejected, setError])
}
