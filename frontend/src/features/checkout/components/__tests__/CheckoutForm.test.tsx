import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { CheckoutForm } from '../CheckoutForm'
import { useCartStore } from '@/store/cartStore'

// Mock subcomponents and hooks that make external calls
vi.mock('../AddressSelector', () => ({
  AddressSelector: ({ onSelect }: { onSelect: (id: number) => void }) => (
    <button onClick={() => onSelect(1)}>Seleccionar dirección</button>
  ),
}))

vi.mock('../PaymentMethodSelector', () => ({
  PaymentMethodSelector: ({ onSelect }: { onSelect: (codigo: string) => void }) => (
    <button onClick={() => onSelect('MERCADOPAGO')}>Seleccionar forma de pago</button>
  ),
}))

vi.mock('../PreCheckoutValidator', () => ({
  usePreCheckoutValidation: () => ({
    status: 'ok' as const,
    diffs: [],
    acceptNewPrices: vi.fn(),
  }),
}))

const mockMutate = vi.fn()

vi.mock('../../hooks/useCrearPedido', () => ({
  useCrearPedido: () => ({
    mutate: mockMutate,
    isPending: false,
  }),
}))

function renderCheckoutForm() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
  return render(
    <MemoryRouter>
      <QueryClientProvider client={qc}>
        <CheckoutForm />
      </QueryClientProvider>
    </MemoryRouter>,
  )
}

describe('CheckoutForm', () => {
  beforeEach(() => {
    useCartStore.getState().clearCart()
    vi.clearAllMocks()
  })

  it('el botón "Confirmar" está deshabilitado si no hay items en el carrito', () => {
    renderCheckoutForm()
    const btn = screen.getByRole('button', { name: /confirmar pedido/i })
    expect(btn).toBeDisabled()
  })

  it('el botón se habilita al tener items, dirección y forma de pago', () => {
    useCartStore.getState().addItem({ id: 1, nombre: 'Pizza', precio_base: 150 }, 1, [], [])
    renderCheckoutForm()

    fireEvent.click(screen.getByRole('button', { name: /seleccionar dirección/i }))
    fireEvent.click(screen.getByRole('button', { name: /seleccionar forma de pago/i }))

    const btn = screen.getByRole('button', { name: /confirmar pedido/i })
    expect(btn).not.toBeDisabled()
  })

  it('dispatch la mutación con el body correcto al confirmar', () => {
    useCartStore.getState().addItem({ id: 7, nombre: 'Pizza', precio_base: 200 }, 2, [], [])
    renderCheckoutForm()

    fireEvent.click(screen.getByRole('button', { name: /seleccionar dirección/i }))
    fireEvent.click(screen.getByRole('button', { name: /seleccionar forma de pago/i }))
    fireEvent.click(screen.getByRole('button', { name: /confirmar pedido/i }))

    expect(mockMutate).toHaveBeenCalledOnce()
    const [body] = mockMutate.mock.calls[0]
    expect(body.direccion_id).toBe(1)
    expect(body.forma_pago_codigo).toBe('MERCADOPAGO')
    expect(body.items).toHaveLength(1)
    expect(body.items[0].producto_id).toBe(7)
    expect(body.items[0].cantidad).toBe(2)
  })
})
