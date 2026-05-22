import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { OrderSummary } from '../OrderSummary'
import { useCartStore } from '@/store/cartStore'

function renderOrderSummary() {
  return render(<OrderSummary />)
}

describe('OrderSummary', () => {
  beforeEach(() => {
    useCartStore.getState().clearCart()
  })

  it('muestra "Resumen del pedido" como título', () => {
    renderOrderSummary()
    expect(screen.getByText(/resumen del pedido/i)).toBeInTheDocument()
  })

  it('muestra cada item con nombre × cantidad y subtotal', () => {
    useCartStore.getState().addItem(
      { id: 1, nombre: 'Pizza Test', precio_base: 150 },
      2,
      [],
      [],
    )
    renderOrderSummary()
    expect(screen.getByText(/pizza test × 2/i)).toBeInTheDocument()
    // subtotal 150 * 2 = 300 (formato ARS) — puede aparecer dos veces (item + total)
    expect(screen.getAllByText(/300/).length).toBeGreaterThan(0)
  })

  it('muestra el total correcto para múltiples items', () => {
    useCartStore.getState().addItem({ id: 1, nombre: 'Pizza', precio_base: 150 }, 2, [], [])
    useCartStore.getState().addItem({ id: 2, nombre: 'Bebida', precio_base: 50 }, 1, [], [])
    renderOrderSummary()
    // total: 150*2 + 50*1 = 350
    const totalEl = screen.getAllByText(/350/)
    expect(totalEl.length).toBeGreaterThan(0)
  })

  it('muestra ingredientes excluidos cuando hay personalizacion', () => {
    useCartStore.getState().addItem(
      { id: 1, nombre: 'Pizza', precio_base: 100 },
      1,
      [5],
      ['Cebolla'],
    )
    renderOrderSummary()
    expect(screen.getByText(/sin: cebolla/i)).toBeInTheDocument()
  })
})
