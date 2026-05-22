import { useNavigate } from 'react-router-dom'
import { useCartStore } from '@/store/cartStore'
import { CheckoutForm } from '@/features/checkout/components/CheckoutForm'

export default function CheckoutPage() {
  const navigate = useNavigate()
  const items = useCartStore((s) => s.items)

  if (items.length === 0) {
    return (
      <main className="max-w-product mx-auto px-4 py-16 flex flex-col items-center gap-4 text-center">
        <p className="text-text-secondary">Tu carrito está vacío.</p>
        <button
          onClick={() => navigate('/catalogo')}
          className="px-6 py-2.5 bg-blue text-white rounded-full text-sm font-medium hover:bg-blue-dark"
        >
          Ir al catálogo
        </button>
      </main>
    )
  }

  return (
    <main className="max-w-product mx-auto px-4 py-10">
      <h1 className="text-2xl font-semibold text-text-primary mb-8">Checkout</h1>
      <CheckoutForm />
    </main>
  )
}
