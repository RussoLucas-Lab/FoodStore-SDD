/**
 * CartBadge — ícono de carrito con badge de cantidad total.
 *
 * Badge se oculta cuando totalItems === 0.
 * Click invoca toggleCart() del uiStore.
 */

import { useUiStore } from '@/store/uiStore'
import { useCartStore, selectTotalItems } from '@/store/cartStore'

export function CartBadge() {
  const toggleCart = useUiStore((s) => s.toggleCart)
  const totalItems = useCartStore(selectTotalItems)

  return (
    <button
      onClick={toggleCart}
      className="relative p-1.5 text-text-secondary hover:text-text-primary transition-colors"
      aria-label={`Carrito de compras${totalItems > 0 ? ` — ${totalItems} items` : ''}`}
    >
      {/* Ícono carrito (SVG inline) */}
      <svg
        xmlns="http://www.w3.org/2000/svg"
        className="h-6 w-6"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={2}
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13l-1.4 5.6A1 1 0 007.6 20h9.8a1 1 0 00.97-1.24L17 13M7 13H5.4M12 17a1 1 0 100 2 1 1 0 000-2zm5 0a1 1 0 100 2 1 1 0 000-2z"
        />
      </svg>

      {/* Badge de cantidad */}
      {totalItems > 0 && (
        <span
          className="absolute -top-1 -right-1 bg-blue text-white text-xs font-bold rounded-full min-w-[18px] h-[18px] flex items-center justify-center px-1 leading-none"
          aria-hidden="true"
        >
          {totalItems > 99 ? '99+' : totalItems}
        </span>
      )}
    </button>
  )
}
