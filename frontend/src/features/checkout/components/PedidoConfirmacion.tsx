import { useLocation, useNavigate } from 'react-router-dom'
import type { PedidoRead } from '@/types/pedidos'

const arsFormatter = new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS' })

interface LocationState {
  pedido?: PedidoRead
}

export function PedidoConfirmacion() {
  const location = useLocation()
  const navigate = useNavigate()
  const state = location.state as LocationState | null
  const pedido = state?.pedido

  if (!pedido) {
    return (
      <div className="flex flex-col items-center gap-4 py-16 px-4 text-center">
        <p className="text-text-secondary text-sm">
          Tu pedido fue creado correctamente. Podés verlo en Mis Pedidos.
        </p>
        <button
          onClick={() => navigate('/pedidos')}
          className="px-6 py-2.5 bg-blue text-white rounded-full text-sm font-medium hover:bg-blue-dark"
        >
          Ver mis pedidos
        </button>
      </div>
    )
  }

  return (
    <div className="flex flex-col items-center gap-6 py-16 px-4 text-center max-w-md mx-auto">
      {/* Ícono de éxito */}
      <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center">
        <svg className="w-8 h-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
        </svg>
      </div>

      <div className="flex flex-col gap-1">
        <h1 className="text-2xl font-semibold text-text-primary">¡Pedido creado!</h1>
        <p className="text-text-secondary text-sm">Tu pedido fue creado correctamente.</p>
      </div>

      <div className="bg-white border border-border-color rounded-xl p-6 w-full flex flex-col gap-3 text-left">
        <div className="flex justify-between text-sm">
          <span className="text-text-secondary">Número de pedido</span>
          <span className="font-semibold text-text-primary">#{pedido.id}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-text-secondary">Estado</span>
          <span className="text-text-primary">{pedido.estado_codigo}</span>
        </div>
        <div className="flex justify-between text-sm font-semibold">
          <span className="text-text-secondary">Total</span>
          <span className="text-text-primary">{arsFormatter.format(Number(pedido.total))}</span>
        </div>
      </div>

      <div className="flex flex-col gap-3 w-full">
        <button
          onClick={() => navigate('/pedidos')}
          className="w-full py-3 bg-blue text-white rounded-full text-sm font-semibold hover:bg-blue-dark"
        >
          Ver mis pedidos
        </button>
        <button
          onClick={() => navigate('/catalogo')}
          className="w-full py-3 border border-border-color text-text-primary rounded-full text-sm font-medium hover:border-blue/40"
        >
          Seguir comprando
        </button>
      </div>
    </div>
  )
}
