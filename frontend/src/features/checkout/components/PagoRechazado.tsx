import { useNavigate } from 'react-router-dom'
import { usePaymentStore } from '@/store/paymentStore'
import { useCartStore } from '@/store/cartStore'
import { apiClient } from '@/api/client'

/**
 * Pantalla de pago rechazado o error.
 * Ofrece opción de reintentar o cancelar el pedido.
 */
export function PagoRechazado() {
  const navigate = useNavigate()
  const status = usePaymentStore((s) => s.status)
  const pedidoId = usePaymentStore((s) => s.pedidoId)
  const errorMsg = usePaymentStore((s) => s.errorMsg)
  const reset = usePaymentStore((s) => s.reset)
  const clearCart = useCartStore((s) => s.clearCart)

  const handleReintentar = () => {
    reset()
    navigate('/checkout')
  }

  const handleCancelarPedido = async () => {
    if (pedidoId) {
      try {
        await apiClient.patch(`/api/v1/pedidos/${pedidoId}/estado`, {
          nuevo_estado: 'CANCELADO',
          motivo: 'Pago rechazado por el usuario',
        })
      } catch {
        // Si falla la cancelación, continuar igual
      }
    }
    clearCart()
    reset()
    navigate('/catalogo')
  }

  const mensaje =
    status === 'rejected'
      ? 'Tu pago no pudo ser procesado por la entidad bancaria.'
      : errorMsg ?? 'Ocurrió un error al procesar tu pago.'

  return (
    <div className="flex flex-col items-center gap-6 py-16 text-center max-w-md mx-auto px-4">
      {/* Ícono error */}
      <div className="w-20 h-20 rounded-full bg-red-100 flex items-center justify-center">
        <svg
          className="w-10 h-10 text-red-500"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M6 18L18 6M6 6l12 12"
          />
        </svg>
      </div>

      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-semibold text-text-primary">Tu pago no pudo procesarse</h1>
        <p className="text-sm text-text-secondary">{mensaje}</p>
        {pedidoId && (
          <p className="text-xs text-text-secondary">Pedido #{pedidoId}</p>
        )}
      </div>

      <div className="flex flex-col gap-3 w-full">
        <button
          onClick={handleReintentar}
          className="w-full py-3 bg-blue text-white rounded-full font-semibold text-sm hover:bg-blue-dark transition-colors"
        >
          Intentar de nuevo
        </button>
        <button
          onClick={handleCancelarPedido}
          className="w-full py-3 border border-error text-error rounded-full font-semibold text-sm hover:bg-red-50 transition-colors"
        >
          Cancelar pedido
        </button>
      </div>
    </div>
  )
}
