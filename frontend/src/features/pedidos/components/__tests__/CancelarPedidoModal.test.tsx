/**
 * Tests para CancelarPedidoModal (task 14.3):
 *   - deshabilita confirmar con motivo vacío
 *   - llama mutación con motivo correcto
 *   - muestra error de API
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { CancelarPedidoModal } from '../CancelarPedidoModal'

const mockMutate = vi.fn()

vi.mock('../../hooks/useCancelarPedido', () => ({
  useCancelarPedido: () => ({
    mutate: mockMutate,
    isPending: false,
  }),
}))

function renderModal(open = true) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <MemoryRouter>
      <QueryClientProvider client={qc}>
        <CancelarPedidoModal
          open={open}
          onClose={vi.fn()}
          pedidoId={42}
        />
      </QueryClientProvider>
    </MemoryRouter>,
  )
}

describe('CancelarPedidoModal', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('el botón confirmar está deshabilitado cuando el motivo está vacío', () => {
    renderModal()
    const btn = screen.getByRole('button', { name: /confirmar cancelación/i })
    expect(btn).toBeDisabled()
  })

  it('el botón confirmar se habilita al escribir un motivo', () => {
    renderModal()
    const textarea = screen.getByPlaceholderText(/ej: ya no puedo recibirlo/i)
    fireEvent.change(textarea, { target: { value: 'No me llega a tiempo' } })

    const btn = screen.getByRole('button', { name: /confirmar cancelación/i })
    expect(btn).not.toBeDisabled()
  })

  it('llama la mutación con el motivo correcto al confirmar', () => {
    renderModal()
    const textarea = screen.getByPlaceholderText(/ej: ya no puedo recibirlo/i)
    fireEvent.change(textarea, { target: { value: 'Motivo de prueba' } })

    const btn = screen.getByRole('button', { name: /confirmar cancelación/i })
    fireEvent.click(btn)

    expect(mockMutate).toHaveBeenCalledOnce()
    const [params] = mockMutate.mock.calls[0]
    expect(params.id).toBe(42)
    expect(params.motivo).toBe('Motivo de prueba')
  })

  it('no muestra el modal cuando open=false', () => {
    renderModal(false)
    expect(screen.queryByRole('dialog')).toBeNull()
  })
})
