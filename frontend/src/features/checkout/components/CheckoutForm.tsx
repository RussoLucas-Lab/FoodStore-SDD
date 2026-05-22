import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useCartStore } from '@/store/cartStore'
import { usePaymentStore } from '@/store/paymentStore'
import { AddressSelector } from './AddressSelector'
import { OrderSummary } from './OrderSummary'
import { PaymentMethodSelector } from './PaymentMethodSelector'
import { usePreCheckoutValidation } from './PreCheckoutValidator'
import { useCrearPedido } from '../hooks/useCrearPedido'
import { CardPayment } from './CardPayment'
import { usePaymentStatus } from '../hooks/usePaymentStatus'

const arsFormatter = new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS' })

export function CheckoutForm() {
  const navigate = useNavigate()
  const items = useCartStore((s) => s.items)
  const [selectedDireccionId, setSelectedDireccionId] = useState<number | null>(null)
  const [selectedFormaPago, setSelectedFormaPago] = useState<string | null>(null)

  // UUID estable durante el ciclo de vida del form para idempotencia
  const idempotencyKey = useMemo(() => crypto.randomUUID(), [])

  const { mutate: crearPedido, isPending } = useCrearPedido(idempotencyKey)
  const { status: validationStatus, diffs, acceptNewPrices } = usePreCheckoutValidation()

  // paymentStore — FSM del pago
  const paymentStatus = usePaymentStore((s) => s.status)
  const paymentPedidoId = usePaymentStore((s) => s.pedidoId)
  const setProcessing = usePaymentStore((s) => s.setProcessing)
  const resetPayment = usePaymentStore((s) => s.reset)

  // Resetear paymentStore al montar
  useEffect(() => {
    resetPayment()
  }, [resetPayment])

  // Polling del estado del pago
  usePaymentStatus(paymentStatus === 'processing' ? paymentPedidoId : null)

  // Redirigir cuando el pago sea aprobado o rechazado
  useEffect(() => {
    if (paymentStatus === 'approved') {
      navigate('/checkout/pago-exitoso')
    } else if (paymentStatus === 'rejected' || paymentStatus === 'error') {
      navigate('/checkout/pago-rechazado')
    }
  }, [paymentStatus, navigate])

  const isDisabled =
    !selectedDireccionId ||
    !selectedFormaPago ||
    items.length === 0 ||
    validationStatus === 'checking' ||
    validationStatus === 'stock-error' ||
    isPending

  const handleSubmit = () => {
    if (!selectedDireccionId || !selectedFormaPago) return

    const pedidoItems = items.map((item) => ({
      producto_id: item.productoId,
      cantidad: item.cantidad,
      personalizacion: item.ingredientesExcluidosIds.length > 0 ? item.ingredientesExcluidosIds : undefined,
    }))

    crearPedido(
      {
        direccion_id: selectedDireccionId,
        forma_pago_codigo: selectedFormaPago,
        items: pedidoItems,
      },
      {
        onSuccess: (data) => {
          // Transicionar paymentStore a 'processing' con el ID del pedido creado
          setProcessing(data.id)
          // No navegar aquí — el CardPayment se renderiza inline
        },
      },
    )
  }

  // Si el pedido fue creado y la forma de pago es MERCADOPAGO, mostrar CardPayment
  if (paymentStatus === 'processing' && paymentPedidoId && selectedFormaPago === 'MERCADOPAGO') {
    return (
      <div className="flex flex-col gap-6 max-w-2xl mx-auto">
        <div className="bg-white rounded-xl border border-border-color p-6">
          <h2 className="text-base font-semibold text-text-primary mb-4">Completá tu pago</h2>
          <p className="text-sm text-text-secondary mb-6">
            Pedido creado exitosamente. Completá el pago con MercadoPago.
          </p>
          <CardPayment pedidoId={paymentPedidoId} />
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-8 max-w-2xl mx-auto">
      {/* Resumen */}
      <section className="bg-white rounded-xl border border-border-color p-6">
        <OrderSummary />
      </section>

      {/* Dirección */}
      <section className="bg-white rounded-xl border border-border-color p-6">
        <h2 className="text-base font-semibold text-text-primary mb-4">Dirección de entrega</h2>
        <AddressSelector selectedId={selectedDireccionId} onSelect={setSelectedDireccionId} />
      </section>

      {/* Forma de pago */}
      <section className="bg-white rounded-xl border border-border-color p-6">
        <h2 className="text-base font-semibold text-text-primary mb-4">Forma de pago</h2>
        <PaymentMethodSelector
          selectedCodigo={selectedFormaPago}
          onSelect={setSelectedFormaPago}
        />
      </section>

      {/* Validación pre-checkout */}
      {validationStatus === 'stock-error' && (
        <div className="bg-red-50 border border-error rounded-xl p-4 text-sm text-error">
          Algunos productos ya no están disponibles o no tienen suficiente stock. Revisá tu carrito.
        </div>
      )}
      {validationStatus === 'price-changed' && diffs.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-400 rounded-xl p-4 text-sm text-yellow-800 flex flex-col gap-2">
          <p className="font-medium">Los precios de algunos productos cambiaron:</p>
          <ul className="list-disc list-inside">
            {diffs.map((d) => (
              <li key={d.productoId}>
                {d.nombre}: {arsFormatter.format(d.precioAnterior)} → {arsFormatter.format(d.precioNuevo)}
              </li>
            ))}
          </ul>
          <button
            onClick={acceptNewPrices}
            className="mt-1 text-blue font-medium hover:underline self-start"
          >
            Actualizar precios y continuar
          </button>
        </div>
      )}

      {/* Botón confirmar */}
      <button
        onClick={handleSubmit}
        disabled={isDisabled}
        className={`w-full py-3 rounded-full font-semibold text-sm transition-colors
          ${isDisabled
            ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
            : 'bg-blue text-white hover:bg-blue-dark'
          }
        `}
      >
        {isPending ? (
          <span className="flex items-center justify-center gap-2">
            <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
            </svg>
            Procesando…
          </span>
        ) : (
          'Confirmar pedido'
        )}
      </button>
    </div>
  )
}
