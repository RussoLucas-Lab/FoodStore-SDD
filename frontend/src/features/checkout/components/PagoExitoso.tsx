import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { usePaymentStore } from '@/store/paymentStore'
import { useCartStore } from '@/store/cartStore'

/**
 * Pantalla de pago aprobado.
 * Muestra ícono check, mensaje de éxito, número de pedido y CTAs.
 */
export function PagoExitoso() {
  const navigate = useNavigate()
  const status = usePaymentStore((s) => s.status)
  const pedidoId = usePaymentStore((s) => s.pedidoId)
  const reset = usePaymentStore((s) => s.reset)
  const items = useCartStore((s) => s.items)
  const clearCart = useCartStore((s) => s.clearCart)

  // Vaciar carrito al montar si aún tiene items
  useEffect(() => {
    if (items.length > 0) {
      clearCart()
    }
  }, [items.length, clearCart])

  // Redirigir si no hay pago aprobado
  if (status !== 'approved') {
    return (
      <div className="flex flex-col items-center gap-4 py-16 text-center">
        <p className="text-text-secondary">No hay pago aprobado.</p>
        <button
          onClick={() => navigate('/pedidos')}
          className="px-5 py-2 bg-blue text-white rounded-full text-sm font-medium hover:bg-blue-dark"
        >
          Ver mis pedidos
        </button>
      </div>
    )
  }

  const handleVerPedido = () => {
    if (pedidoId) {
      reset()
      navigate(`/pedidos/${pedidoId}`)
    } else {
      reset()
      navigate('/pedidos')
    }
  }

  const handleSeguirComprando = () => {
    reset()
    navigate('/catalogo')
  }

  return (
    <div className="flex flex-col items-center gap-6 py-16 text-center max-w-md mx-auto px-4">
      {/* Ícono check */}
      <div className="w-20 h-20 rounded-full bg-green-100 flex items-center justify-center">
        <svg
          className="w-10 h-10 text-green-500"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
        </svg>
      </div>

      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-semibold text-text-primary">¡Tu pago fue aprobado!</h1>
        {pedidoId && (
          <p className="text-text-secondary">Pedido #{pedidoId}</p>
        )}
        <p className="text-sm text-text-secondary">
          Recibirás una confirmación con los detalles de tu compra.
        </p>
      </div>

      <div className="flex flex-col gap-3 w-full">
        {pedidoId && (
          <button
            onClick={handleVerPedido}
            className="w-full py-3 bg-blue text-white rounded-full font-semibold text-sm hover:bg-blue-dark transition-colors"
          >
            Ver mi pedido
          </button>
        )}
        <button
          onClick={handleSeguirComprando}
          className="w-full py-3 border border-border-color text-text-primary rounded-full font-semibold text-sm hover:bg-gray-50 transition-colors"
        >
          Seguir comprando
        </button>
      </div>
    </div>
  )
}
