/**
 * Tests para PedidosList (task 14.1):
 *   - renderiza cards con datos
 *   - muestra empty state
 *   - muestra skeletons durante carga
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { PedidosList } from '../PedidosList'

// Mock del hook usePedidos
vi.mock('../../hooks/usePedidos', () => ({
  usePedidos: vi.fn(),
}))

import { usePedidos } from '../../hooks/usePedidos'

const mockUsePedidos = vi.mocked(usePedidos)

function renderWithProviders(ui: React.ReactElement) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <MemoryRouter>
      <QueryClientProvider client={qc}>{ui}</QueryClientProvider>
    </MemoryRouter>,
  )
}

describe('PedidosList', () => {
  it('muestra skeletons mientras carga', () => {
    mockUsePedidos.mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
    } as ReturnType<typeof usePedidos>)

    renderWithProviders(<PedidosList />)

    // Hay elementos con aria-hidden (skeletons)
    const skeletons = document.querySelectorAll('[aria-hidden="true"]')
    expect(skeletons.length).toBeGreaterThan(0)
  })

  it('muestra empty state con CTA al catálogo cuando no hay pedidos', () => {
    mockUsePedidos.mockReturnValue({
      data: { items: [], total: 0, page: 1, size: 10, pages: 0 },
      isLoading: false,
      isError: false,
    } as ReturnType<typeof usePedidos>)

    renderWithProviders(<PedidosList />)

    expect(screen.getByText(/no realizaste ningún pedido/i)).toBeTruthy()
    expect(screen.getByRole('link', { name: /ver catálogo/i })).toBeTruthy()
  })

  it('renderiza cards con datos del pedido', () => {
    const pedidos = [
      { id: 101, estado_codigo: 'PENDIENTE', total: 1500, created_at: '2026-05-01T10:00:00Z' },
      { id: 102, estado_codigo: 'ENTREGADO', total: 2300, created_at: '2026-04-15T09:00:00Z' },
    ]

    mockUsePedidos.mockReturnValue({
      data: { items: pedidos, total: 2, page: 1, size: 10, pages: 1 },
      isLoading: false,
      isError: false,
    } as ReturnType<typeof usePedidos>)

    renderWithProviders(<PedidosList />)

    expect(screen.getByText('Pedido #101')).toBeTruthy()
    expect(screen.getByText('Pedido #102')).toBeTruthy()
    expect(screen.getAllByText(/Pendiente/i).length).toBeGreaterThan(0)
    expect(screen.getAllByText(/Entregado/i).length).toBeGreaterThan(0)
  })
})
