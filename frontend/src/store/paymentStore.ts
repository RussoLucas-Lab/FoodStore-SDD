/**
 * paymentStore — FSM de estado de pago con MercadoPago.
 *
 * NO persiste en localStorage (el estado de pago es efímero).
 * Se resetea a 'idle' al montar CheckoutForm.
 *
 * Convención: suscribirse por slice.
 * Ejemplo: const status = usePaymentStore(s => s.status)
 *
 * Estados posibles:
 *   idle       → estado inicial, sin pago en progreso
 *   processing → pedido creado, esperando respuesta del pago
 *   approved   → pago aprobado por MercadoPago
 *   rejected   → pago rechazado
 *   error      → error de red o HTTP 5xx
 */

import { create } from 'zustand'

export type PaymentStatus = 'idle' | 'processing' | 'approved' | 'rejected' | 'error'

interface PaymentStore {
  status: PaymentStatus
  pedidoId: number | null
  errorMsg: string | null

  /** Transiciona a 'processing' cuando el pedido fue creado exitosamente. */
  setProcessing: (pedidoId: number) => void

  /** Transiciona a 'approved' cuando el polling detecta pago aprobado. */
  setApproved: () => void

  /** Transiciona a 'rejected' cuando el polling detecta pago rechazado. */
  setRejected: () => void

  /** Transiciona a 'error' con mensaje descriptivo. */
  setError: (msg: string) => void

  /** Resetea el store al estado inicial 'idle'. */
  reset: () => void
}

export const usePaymentStore = create<PaymentStore>()((set) => ({
  status: 'idle',
  pedidoId: null,
  errorMsg: null,

  setProcessing: (pedidoId: number) =>
    set({ status: 'processing', pedidoId, errorMsg: null }),

  setApproved: () =>
    set({ status: 'approved' }),

  setRejected: () =>
    set({ status: 'rejected' }),

  setError: (msg: string) =>
    set({ status: 'error', errorMsg: msg }),

  reset: () =>
    set({ status: 'idle', pedidoId: null, errorMsg: null }),
}))
