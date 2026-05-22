import { useEffect } from 'react'
import { initMercadoPago, Payment } from '@mercadopago/sdk-react'
import { useCrearPreferencia } from '../hooks/useCrearPreferencia'
import { Spinner } from '@/components/Spinner'

interface CardPaymentProps {
  pedidoId: number
}

const MP_PUBLIC_KEY = import.meta.env.VITE_MP_PUBLIC_KEY ?? ''

/**
 * Componente de pago con MercadoPago SDK React.
 *
 * Al montar, llama POST /api/v1/pagos/crear para obtener el preferenceId.
 * Renderiza el brick de MercadoPago con ese preferenceId.
 */
export function CardPayment({ pedidoId }: CardPaymentProps) {
  const { mutate: crearPreferencia, data, isPending, isError, reset } = useCrearPreferencia()

  useEffect(() => {
    if (MP_PUBLIC_KEY) {
      initMercadoPago(MP_PUBLIC_KEY, { locale: 'es-AR' })
    }
    crearPreferencia(pedidoId)
  }, [pedidoId, crearPreferencia])

  if (isPending) {
    return (
      <div className="flex flex-col items-center gap-4 py-8">
        <Spinner />
        <p className="text-text-secondary text-sm">Preparando el pago…</p>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="flex flex-col items-center gap-4 py-6 text-center">
        <p className="text-error text-sm">No se pudo iniciar el pago. Intentá de nuevo.</p>
        <button
          onClick={() => { reset(); crearPreferencia(pedidoId) }}
          className="px-5 py-2 bg-blue text-white rounded-full text-sm font-medium hover:bg-blue-dark"
        >
          Reintentar
        </button>
      </div>
    )
  }

  if (!data?.preference_id) {
    return (
      <div className="flex flex-col items-center gap-4 py-8">
        <Spinner />
        <p className="text-text-secondary text-sm">Cargando formulario de pago…</p>
      </div>
    )
  }

  // Si hay clave pública, renderizar el brick de MercadoPago
  if (MP_PUBLIC_KEY) {
    return (
      <div className="w-full">
        <Payment
          initialization={{
            amount: 0,
            preferenceId: data.preference_id,
          }}
          customization={{
            paymentMethods: {
              creditCard: 'all',
              debitCard: 'all',
            },
          }}
          onSubmit={async () => Promise.resolve()}
          onError={(error) => {
            console.error('MP error:', error)
          }}
        />
      </div>
    )
  }

  // Fallback: mostrar link directo de MercadoPago (modo desarrollo sin clave pública)
  return (
    <div className="flex flex-col items-center gap-4 py-6 text-center">
      <p className="text-text-secondary text-sm">
        Hacé clic para completar el pago en MercadoPago:
      </p>
      <a
        href={data.init_point}
        target="_blank"
        rel="noopener noreferrer"
        className="px-6 py-3 bg-blue text-white rounded-full font-semibold text-sm hover:bg-blue-dark"
      >
        Pagar con MercadoPago
      </a>
    </div>
  )
}
