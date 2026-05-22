import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { PaymentMethodSelector } from '../PaymentMethodSelector'

vi.mock('../../hooks/useFormasPago', () => ({
  useFormasPago: () => ({
    data: [
      { codigo: 'MERCADOPAGO', descripcion: 'MercadoPago' },
      { codigo: 'EFECTIVO', descripcion: 'Efectivo' },
      { codigo: 'TRANSFERENCIA', descripcion: 'Transferencia' },
    ],
    isLoading: false,
    isError: false,
    refetch: vi.fn(),
  }),
}))

function renderSelector(selectedCodigo: string | null, onSelect = vi.fn()) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return {
    onSelect,
    ...render(
      <QueryClientProvider client={qc}>
        <PaymentMethodSelector selectedCodigo={selectedCodigo} onSelect={onSelect} />
      </QueryClientProvider>,
    ),
  }
}

describe('PaymentMethodSelector', () => {
  it('muestra las 3 formas de pago mockeadas', () => {
    renderSelector(null)
    expect(screen.getByText('MercadoPago')).toBeInTheDocument()
    expect(screen.getByText('Efectivo')).toBeInTheDocument()
    expect(screen.getByText('Transferencia')).toBeInTheDocument()
  })

  it('invoca onSelect al hacer click en una opción', () => {
    const onSelect = vi.fn()
    renderSelector(null, onSelect)
    fireEvent.click(screen.getByText('Efectivo'))
    expect(onSelect).toHaveBeenCalledWith('EFECTIVO')
  })

  it('marca la opción seleccionada con aria-checked=true', () => {
    renderSelector('MERCADOPAGO')
    const radioMp = screen.getByRole('radio', { name: /mercadopago/i })
    expect(radioMp).toHaveAttribute('aria-checked', 'true')
  })

  it('el resto de opciones tienen aria-checked=false', () => {
    renderSelector('MERCADOPAGO')
    const radioEfectivo = screen.getByRole('radio', { name: /efectivo/i })
    expect(radioEfectivo).toHaveAttribute('aria-checked', 'false')
  })
})
