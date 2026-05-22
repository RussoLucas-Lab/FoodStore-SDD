/**
 * CartItemCard — render de un renglón del carrito.
 *
 * Muestra: nombre, precio, lista de exclusiones, botones +/−/Eliminar, subtotal.
 */

import { useCartStore } from '@/store/cartStore'
import type { CartItem } from '@/types/carrito'

const arsFormatter = new Intl.NumberFormat('es-AR', {
  style: 'currency',
  currency: 'ARS',
})

interface CartItemCardProps {
  item: CartItem
}

export function CartItemCard({ item }: CartItemCardProps) {
  const updateCantidad = useCartStore((s) => s.updateCantidad)
  const removeItem = useCartStore((s) => s.removeItem)

  const subtotal = item.precio * item.cantidad

  return (
    <div className="flex flex-col gap-1 p-3 border border-border-color rounded-md bg-surface">
      {/* Nombre y precio */}
      <div className="flex items-start justify-between gap-2">
        <span className="text-text-primary font-medium text-sm leading-tight flex-1">
          {item.nombre}
        </span>
        <span className="text-text-secondary text-sm whitespace-nowrap">
          {arsFormatter.format(item.precio)} c/u
        </span>
      </div>

      {/* Ingredientes excluidos */}
      {item.ingredientesExcluidosNombres.length > 0 && (
        <p className="text-xs text-text-secondary">
          Sin: {item.ingredientesExcluidosNombres.join(', ')}
        </p>
      )}

      {/* Controles de cantidad y subtotal */}
      <div className="flex items-center justify-between gap-2 mt-1">
        {/* Botones cantidad */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => updateCantidad(item.lineId, item.cantidad - 1)}
            disabled={item.cantidad <= 1}
            className="w-7 h-7 rounded-full border border-border-color flex items-center justify-center text-text-secondary hover:bg-surface-alt disabled:opacity-40 transition-colors"
            aria-label="Disminuir cantidad"
          >
            −
          </button>
          <span className="text-text-primary font-medium text-sm w-5 text-center">
            {item.cantidad}
          </span>
          <button
            onClick={() => updateCantidad(item.lineId, item.cantidad + 1)}
            className="w-7 h-7 rounded-full border border-border-color flex items-center justify-center text-text-secondary hover:bg-surface-alt transition-colors"
            aria-label="Aumentar cantidad"
          >
            +
          </button>
        </div>

        {/* Subtotal + Eliminar */}
        <div className="flex items-center gap-3">
          <span className="text-text-primary font-semibold text-sm">
            {arsFormatter.format(subtotal)}
          </span>
          <button
            onClick={() => removeItem(item.lineId)}
            className="text-error text-xs hover:underline"
            aria-label={`Eliminar ${item.nombre}`}
          >
            Eliminar
          </button>
        </div>
      </div>
    </div>
  )
}
