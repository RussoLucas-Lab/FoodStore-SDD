/**
 * Tests para GestionPedidosTable (task 14.4):
 *   - filtros de estado
 *   - búsqueda por id
 *   - redirige si rol no autorizado (via ProtectedRoute en la página, no aquí)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { GestionPedidosTable } from '../GestionPedidosTable'

vi.mock('../../hooks/useGestionPedidos', () => ({
  useGestionPedidos: vi.fn(),
}))

vi.mock('../../hooks/useAvanzarEstado', () => ({
  useAvanzarEstado: () => ({
    mutate: vi.fn(),
    isPending: false,
  }),
}))

// Mock EstadoPedidoBadge
vi.mock('@/features/pedidos/components/EstadoPedidoBadge', () => ({
  EstadoPedidoBadge: ({ estado }: { estado: string }) => <span>{estado}</span>,
}))

import { useGestionPedidos } from '../../hooks/useGestionPedidos'

const mockUseGestionPedidos = vi.mocked(useGestionPedidos)

const pedidosMock = [
  { id: 1, estado_codigo: 'PENDIENTE', total: 1000, created_at: '2026-05-01T10:00:00Z' },
  { id: 2, estado_codigo: 'CONFIRMADO', total: 2000, created_at: '2026-05-02T10:00:00Z' },
  { id: 3, estado_codigo: 'ENTREGADO', total: 500, created_at: '2026-04-01T10:00:00Z' },
]

function renderTable() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <MemoryRouter>
      <QueryClientProvider client={qc}>
        <GestionPedidosTable />
      </QueryClientProvider>
    </MemoryRouter>,
  )
}

describe('GestionPedidosTable', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockUseGestionPedidos.mockReturnValue({
      data: { items: pedidosMock, total: 3, page: 1, size: 15, pages: 1 },
      isLoading: false,
      isError: false,
    } as ReturnType<typeof useGestionPedidos>)
  })

  it('renderiza los pedidos en la tabla', () => {
    renderTable()
    expect(screen.getByText('#1')).toBeTruthy()
    expect(screen.getByText('#2')).toBeTruthy()
    expect(screen.getByText('#3')).toBeTruthy()
  })

  it('filtra por id al escribir en el buscador', () => {
    renderTable()
    const input = screen.getByPlaceholderText(/buscar por id/i)
    fireEvent.change(input, { target: { value: '2' } })

    // Pedido con id 2 sigue visible
    expect(screen.getByText('#2')).toBeTruthy()
    // Pedido con id 3 debería desaparecer del DOM filtrado
    expect(screen.queryByText('#3')).toBeNull()
  })

  it('el botón Avanzar está deshabilitado para estados terminales', () => {
    renderTable()
    const rows = screen.getAllByRole('row')
    // La fila de ENTREGADO (pedido #3) debe tener el botón Avanzar deshabilitado
    const entregadoRow = rows.find((r) => r.textContent?.includes('#3'))
    const btn = entregadoRow?.querySelector('button')
    expect(btn).toBeDefined()
    expect(btn?.disabled).toBe(true)
  })

  it('el botón Avanzar está habilitado para estados no terminales (CONFIRMADO)', () => {
    renderTable()
    const rows = screen.getAllByRole('row')
    const confirmadoRow = rows.find((r) => r.textContent?.includes('#2'))
    const btn = confirmadoRow?.querySelector('button')
    expect(btn).toBeDefined()
    expect(btn?.disabled).toBe(false)
  })
})
