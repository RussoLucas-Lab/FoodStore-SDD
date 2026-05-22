/**
 * Tests para PedidoDetail (task 14.2):
 *   - renderiza secciones correctamente
 *   - muestra botón cancelar solo si PENDIENTE
 *   - oculta botón cancelar en otros estados
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { PedidoDetail } from '../PedidoDetail'

vi.mock('../../hooks/usePedido', () => ({
  usePedido: vi.fn(),
}))

// Mock PaymentStatus to avoid real query
vi.mock('../PaymentStatus', () => ({
  PaymentStatus: () => <span>Estado de pago</span>,
}))

import { usePedido } from '../../hooks/usePedido'

const mockUsePedido = vi.mocked(usePedido)

const pedidoBase = {
  id: 1,
  estado_codigo: 'PENDIENTE',
  total: 500,
  created_at: '2026-05-01T10:00:00Z',
  direccion_snapshot: {
    calle: 'Corrientes',
    numero: '1234',
    ciudad: 'CABA',
    provincia: 'Buenos Aires',
    codigo_postal: 'C1043',
  },
  items: [
    {
      id: 10,
      producto_id: 1,
      nombre_snapshot: 'Pizza Margherita',
      precio_snapshot: 500,
      cantidad: 1,
      personalizacion: null,
    },
  ],
  historial: [
    {
      id: 1,
      estado_desde: null,
      estado_hasta: 'PENDIENTE',
      cambiado_por_id: 1,
      motivo: null,
      created_at: '2026-05-01T10:00:00Z',
    },
  ],
  pago: null,
}

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

describe('PedidoDetail', () => {
  it('renderiza las secciones correctamente', () => {
    mockUsePedido.mockReturnValue({
      data: pedidoBase,
      isLoading: false,
      isError: false,
    } as ReturnType<typeof usePedido>)

    renderWithProviders(<PedidoDetail pedidoId={1} />)

    expect(screen.getByText(/Pizza Margherita/i)).toBeTruthy()
    expect(screen.getByText(/Corrientes/i)).toBeTruthy()
    expect(screen.getByText(/Historial de estados/i)).toBeTruthy()
    expect(screen.getByText(/Pedido creado/i)).toBeTruthy()
  })

  it('muestra botón cancelar si estado es PENDIENTE', () => {
    mockUsePedido.mockReturnValue({
      data: { ...pedidoBase, estado_codigo: 'PENDIENTE' },
      isLoading: false,
      isError: false,
    } as ReturnType<typeof usePedido>)

    renderWithProviders(<PedidoDetail pedidoId={1} />)

    expect(screen.getByRole('button', { name: /cancelar pedido/i })).toBeTruthy()
  })

  it('oculta botón cancelar si estado no es PENDIENTE', () => {
    mockUsePedido.mockReturnValue({
      data: { ...pedidoBase, estado_codigo: 'CONFIRMADO' },
      isLoading: false,
      isError: false,
    } as ReturnType<typeof usePedido>)

    renderWithProviders(<PedidoDetail pedidoId={1} />)

    expect(screen.queryByRole('button', { name: /cancelar pedido/i })).toBeNull()
  })

  it('oculta botón cancelar en estado ENTREGADO', () => {
    mockUsePedido.mockReturnValue({
      data: { ...pedidoBase, estado_codigo: 'ENTREGADO' },
      isLoading: false,
      isError: false,
    } as ReturnType<typeof usePedido>)

    renderWithProviders(<PedidoDetail pedidoId={1} />)

    expect(screen.queryByRole('button', { name: /cancelar pedido/i })).toBeNull()
  })
})
