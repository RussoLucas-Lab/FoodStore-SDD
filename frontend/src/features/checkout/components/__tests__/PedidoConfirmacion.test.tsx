import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { PedidoConfirmacion } from '../PedidoConfirmacion'
import type { PedidoRead } from '@/types/pedidos'

const pedidoMock: PedidoRead = {
  id: 42,
  estado_codigo: 'PENDIENTE',
  total: 530.50,
  created_at: '2026-05-21T12:00:00Z',
}

function renderWithState(state?: { pedido?: PedidoRead }) {
  return render(
    <MemoryRouter initialEntries={[{ pathname: '/checkout/confirmado', state }]}>
      <Routes>
        <Route path="/checkout/confirmado" element={<PedidoConfirmacion />} />
        <Route path="/pedidos" element={<div>Mis Pedidos</div>} />
        <Route path="/catalogo" element={<div>Catalogo</div>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('PedidoConfirmacion', () => {
  it('muestra el número de pedido cuando hay state', () => {
    renderWithState({ pedido: pedidoMock })
    expect(screen.getByText(/#42/)).toBeInTheDocument()
  })

  it('muestra el total formateado', () => {
    renderWithState({ pedido: pedidoMock })
    expect(screen.getByText(/530/)).toBeInTheDocument()
  })

  it('muestra el estado del pedido', () => {
    renderWithState({ pedido: pedidoMock })
    expect(screen.getByText('PENDIENTE')).toBeInTheDocument()
  })

  it('muestra fallback cuando no hay state', () => {
    renderWithState(undefined)
    expect(screen.getByText(/tu pedido fue creado/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /ver mis pedidos/i })).toBeInTheDocument()
  })

  it('muestra los dos CTAs cuando hay pedido', () => {
    renderWithState({ pedido: pedidoMock })
    expect(screen.getByRole('button', { name: /ver mis pedidos/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /seguir comprando/i })).toBeInTheDocument()
  })
})
