import { useCartStore, selectTotalPrice } from '@/store/cartStore'

const arsFormatter = new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS' })

export function OrderSummary() {
  const items = useCartStore((s) => s.items)
  const total = useCartStore(selectTotalPrice)

  return (
    <div className="flex flex-col gap-3">
      <h2 className="text-base font-semibold text-text-primary">Resumen del pedido</h2>
      <div className="flex flex-col gap-2">
        {items.map((item) => (
          <div key={item.lineId} className="flex flex-col gap-0.5">
            <div className="flex items-center justify-between text-sm text-text-primary">
              <span>
                {item.nombre} × {item.cantidad}
              </span>
              <span>{arsFormatter.format(item.precio * item.cantidad)}</span>
            </div>
            {item.ingredientesExcluidosNombres.length > 0 && (
              <p className="text-xs text-text-secondary pl-1">
                Sin: {item.ingredientesExcluidosNombres.join(', ')}
              </p>
            )}
          </div>
        ))}
      </div>
      <div className="flex items-center justify-between pt-2 border-t border-border-color font-semibold text-text-primary">
        <span>Total</span>
        <span>{arsFormatter.format(total)}</span>
      </div>
    </div>
  )
}
