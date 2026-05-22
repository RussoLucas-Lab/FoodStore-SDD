/**
 * CartDrawer — sidebar deslizable desde la derecha.
 *
 * Controlado por useUiStore(s => s.cartOpen).
 * Se monta una vez en el layout raíz y se muestra/oculta con CSS.
 */

import { useNavigate } from 'react-router-dom'
import { useUiStore } from '@/store/uiStore'
import { useCartStore, selectTotalItems, selectTotalPrice } from '@/store/cartStore'
import { CartItemCard } from './CartItemCard'

const arsFormatter = new Intl.NumberFormat('es-AR', {
  style: 'currency',
  currency: 'ARS',
})

export function CartDrawer() {
  const navigate = useNavigate()
  const cartOpen = useUiStore((s) => s.cartOpen)
  const closeCart = useUiStore((s) => s.closeCart)

  const items = useCartStore((s) => s.items)
  const clearCart = useCartStore((s) => s.clearCart)
  const totalItems = useCartStore(selectTotalItems)
  const totalPrice = useCartStore(selectTotalPrice)

  const handleVaciar = () => {
    if (window.confirm('¿Estás seguro de que querés vaciar el carrito?')) {
      clearCart()
    }
  }

  return (
    <>
      {/* Overlay */}
      {cartOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm"
          onClick={closeCart}
          aria-hidden="true"
        />
      )}

      {/* Drawer panel */}
      <aside
        className={`fixed top-0 right-0 z-50 h-full w-full max-w-sm bg-white shadow-modal flex flex-col
          transform transition-transform duration-300 ease-in-out
          ${cartOpen ? 'translate-x-0' : 'translate-x-full'}
        `}
        aria-label="Carrito de compras"
        role="complementary"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-border-color">
          <h2 className="text-text-primary font-semibold text-base">
            Carrito{totalItems > 0 ? ` (${totalItems})` : ''}
          </h2>
          <button
            onClick={closeCart}
            className="text-text-secondary hover:text-text-primary transition-colors"
            aria-label="Cerrar carrito"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-5 w-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Lista de items */}
        <div className="flex-1 overflow-y-auto px-4 py-3 flex flex-col gap-3">
          {items.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full gap-3 text-text-secondary">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-12 w-12 opacity-30"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={1.5}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13l-1.4 5.6A1 1 0 007.6 20h9.8a1 1 0 00.97-1.24L17 13M7 13H5.4"
                />
              </svg>
              <p className="text-sm">Tu carrito está vacío</p>
            </div>
          ) : (
            items.map((item) => <CartItemCard key={item.lineId} item={item} />)
          )}
        </div>

        {/* Footer con totales y acciones */}
        <div className="border-t border-border-color px-5 py-4 flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <span className="text-text-secondary text-sm">Total</span>
            <span className="text-text-primary font-bold text-lg">
              {arsFormatter.format(totalPrice)}
            </span>
          </div>

          <button
            disabled={items.length === 0}
            className={`w-full text-center bg-blue text-white font-medium py-2.5 rounded-full text-sm transition-colors
              ${items.length === 0 ? 'opacity-50 cursor-not-allowed' : 'hover:bg-blue-dark'}
            `}
            onClick={() => {
              closeCart()
              navigate('/checkout')
            }}
          >
            Ir a checkout
          </button>

          {items.length > 0 && (
            <button
              onClick={handleVaciar}
              className="text-error text-sm hover:underline self-center"
            >
              Vaciar carrito
            </button>
          )}
        </div>
      </aside>
    </>
  )
}
