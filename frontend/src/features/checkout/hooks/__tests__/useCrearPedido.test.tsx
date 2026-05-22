import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import type { ReactNode } from 'react'
import { useCrearPedido } from '../useCrearPedido'
import { useCartStore } from '@/store/cartStore'
import { useUiStore } from '@/store/uiStore'

const mockNavigate = vi.fn()
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react-router-dom')>()
  return { ...actual, useNavigate: () => mockNavigate }
})

vi.mock('@/api/endpoints/pedidos', () => ({
  crearPedido: vi.fn(),
}))

const { crearPedido: mockCrearPedidoApi } = await import('@/api/endpoints/pedidos')

function wrapper({ children }: { children: ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
  return (
    <MemoryRouter>
      <QueryClientProvider client={qc}>{children}</QueryClientProvider>
    </MemoryRouter>
  )
}

const pedidoResponse = { id: 99, estado_codigo: 'PENDIENTE', total: 300, created_at: '2026-05-21T12:00:00Z' }

describe('useCrearPedido — integración', () => {
  beforeEach(() => {
    useCartStore.getState().clearCart()
    vi.clearAllMocks()
  })

  it('onSuccess: limpia el carrito y navega a /checkout/confirmado', async () => {
    vi.mocked(mockCrearPedidoApi).mockResolvedValueOnce(pedidoResponse)
    useCartStore.getState().addItem({ id: 1, nombre: 'Pizza', precio_base: 100 }, 2, [], [])

    const { result } = renderHook(() => useCrearPedido('test-key-123'), { wrapper })

    act(() => {
      result.current.mutate({
        direccion_id: 1,
        forma_pago_codigo: 'MERCADOPAGO',
        items: [{ producto_id: 1, cantidad: 2 }],
      })
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    // Carrito vaciado
    expect(useCartStore.getState().items).toHaveLength(0)

    // Navegó al confirmado con el pedido como state
    expect(mockNavigate).toHaveBeenCalledWith('/checkout/confirmado', {
      state: { pedido: pedidoResponse },
    })
  })

  it('onError: muestra toast y NO limpia el carrito', async () => {
    const addToastSpy = vi.spyOn(useUiStore.getState(), 'addToast')
    vi.mocked(mockCrearPedidoApi).mockRejectedValueOnce({
      response: { data: { detail: 'Stock insuficiente' } },
    })
    useCartStore.getState().addItem({ id: 1, nombre: 'Pizza', precio_base: 100 }, 1, [], [])

    const { result } = renderHook(() => useCrearPedido('test-key-456'), { wrapper })

    act(() => {
      result.current.mutate({ direccion_id: 1, forma_pago_codigo: 'MERCADOPAGO', items: [{ producto_id: 1, cantidad: 1 }] })
    })

    await waitFor(() => expect(result.current.isError).toBe(true))

    expect(useCartStore.getState().items).toHaveLength(1)
    expect(addToastSpy).toHaveBeenCalledWith('Stock insuficiente', 'error')
  })
})
