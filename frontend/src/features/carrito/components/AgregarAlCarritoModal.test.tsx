/**
 * Tests para AgregarAlCarritoModal.
 *
 * Cubre:
 * - Modal con 4 ingredientes permite excluir hasta 3
 * - El 4to checkbox queda deshabilitado al llegar al tope
 * - Modal sin ingredientes muestra mensaje y solo permite cantidad
 * - Confirmación llama addItem con args correctos
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { AgregarAlCarritoModal } from '@/features/catalogo/components/AgregarAlCarritoModal'
import type { ProductoRead } from '@/types/productos'

// Mock del cartStore addItem
const mockAddItem = vi.fn()

vi.mock('@/store/cartStore', () => ({
  useCartStore: (selector: (s: { addItem: typeof mockAddItem }) => unknown) =>
    selector({ addItem: mockAddItem }),
  buildLineId: (id: number, ids: number[]) =>
    `${id}::${[...ids].sort((a, b) => a - b).join(',')}`,
  selectTotalItems: (s: { items: unknown[] }) => s.items.length,
  selectTotalPrice: () => 0,
}))

function makeProducto(ingredientesCount: number): ProductoRead {
  return {
    id: 1,
    nombre: 'Pizza Test',
    descripcion: null,
    precio_base: 1500,
    stock_cantidad: 10,
    disponible: true,
    imagen_url: null,
    created_at: '2026-01-01T00:00:00Z',
    deleted_at: null,
    categorias: [],
    ingredientes: Array.from({ length: ingredientesCount }, (_, i) => ({
      id: i + 1,
      nombre: `Ingrediente ${i + 1}`,
      es_alergeno: false,
    })),
  }
}

const mockOnClose = vi.fn()

function renderModal(producto: ProductoRead, open = true) {
  return render(
    <AgregarAlCarritoModal
      producto={producto}
      open={open}
      onClose={mockOnClose}
    />,
  )
}

describe('AgregarAlCarritoModal', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('muestra "Este producto no tiene ingredientes personalizables" cuando no hay ingredientes', () => {
    const producto = makeProducto(0)
    renderModal(producto)

    expect(
      screen.getByText('Este producto no tiene ingredientes personalizables.'),
    ).toBeTruthy()
  })

  it('modal sin ingredientes solo permite ajustar cantidad', () => {
    const producto = makeProducto(0)
    renderModal(producto)

    expect(screen.queryByRole('checkbox')).toBeNull()
    // Botón de cantidad debe existir
    expect(screen.getAllByRole('button').length).toBeGreaterThan(0)
  })

  it('permite excluir hasta n-1 ingredientes (RN-CR04)', () => {
    const producto = makeProducto(4) // 4 ingredientes → máximo 3 excluibles
    renderModal(producto)

    const checkboxes = screen.getAllByRole('checkbox')
    expect(checkboxes).toHaveLength(4)

    // Marcar los primeros 3
    fireEvent.click(checkboxes[0])
    fireEvent.click(checkboxes[1])
    fireEvent.click(checkboxes[2])

    // El 4to checkbox debe quedar deshabilitado
    expect(checkboxes[3]).toBeDisabled()
  })

  it('el 4to checkbox se habilita al desmarcar uno', () => {
    const producto = makeProducto(4)
    renderModal(producto)

    const checkboxes = screen.getAllByRole('checkbox')

    // Marcar los primeros 3
    fireEvent.click(checkboxes[0])
    fireEvent.click(checkboxes[1])
    fireEvent.click(checkboxes[2])

    // El 4to está deshabilitado
    expect(checkboxes[3]).toBeDisabled()

    // Desmarcar el primero → el 4to se habilita
    fireEvent.click(checkboxes[0])
    expect(checkboxes[3]).not.toBeDisabled()
  })

  it('confirmación llama addItem con los args correctos', () => {
    const producto = makeProducto(3)
    renderModal(producto)

    const checkboxes = screen.getAllByRole('checkbox')

    // Excluir ingrediente 1 y 2
    fireEvent.click(checkboxes[0]) // id=1
    fireEvent.click(checkboxes[1]) // id=2

    // Hacer click en "Agregar al carrito"
    const confirmarBtn = screen.getByText('Agregar al carrito')
    fireEvent.click(confirmarBtn)

    expect(mockAddItem).toHaveBeenCalledOnce()
    const [productoArg, cantidadArg, idsArg] = mockAddItem.mock.calls[0] as [
      { id: number; nombre: string; precio_base: number },
      number,
      number[],
    ]
    expect(productoArg.id).toBe(1)
    expect(cantidadArg).toBe(1) // cantidad inicial
    expect(idsArg).toContain(1)
    expect(idsArg).toContain(2)
    expect(idsArg).toHaveLength(2)
  })

  it('cantidad no puede bajar de 1 (botón − deshabilitado)', () => {
    const producto = makeProducto(2)
    renderModal(producto)

    // Buscar el botón de disminuir cantidad por aria-label
    const decreaseBtn = screen.getByLabelText('Disminuir cantidad')
    expect(decreaseBtn).toBeDisabled()
  })

  it('cancel llama onClose sin disparar addItem', () => {
    const producto = makeProducto(2)
    renderModal(producto)

    const cancelBtn = screen.getByText('Cancelar')
    fireEvent.click(cancelBtn)

    expect(mockOnClose).toHaveBeenCalledOnce()
    expect(mockAddItem).not.toHaveBeenCalled()
  })
})
