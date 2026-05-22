/**
 * Tests unitarios para cartStore.
 * Cubre: RN-CR01 (persistencia), RN-CR02 (consolidación por lineId),
 * RN-CR03 (cantidad mínima), selectores derivados.
 */

import { describe, it, expect, beforeEach } from 'vitest'
import { useCartStore, buildLineId, selectTotalItems, selectTotalPrice } from '@/store/cartStore'

const productoA = { id: 1, nombre: 'Pizza Margarita', precio_base: 1500 }
const productoB = { id: 2, nombre: 'Hamburguesa', precio_base: 2000 }

function resetStore() {
  useCartStore.setState({ items: [] })
}

describe('cartStore', () => {
  beforeEach(() => {
    resetStore()
  })

  // -------------------------------------------------------------------------
  // buildLineId
  // -------------------------------------------------------------------------

  describe('buildLineId', () => {
    it('genera lineId con exclusiones vacías', () => {
      expect(buildLineId(1, [])).toBe('1::')
    })

    it('genera lineId con exclusiones', () => {
      expect(buildLineId(1, [3, 1, 2])).toBe('1::1,2,3')
    })

    it('ordena exclusiones para normalización (RN-CR02)', () => {
      const a = buildLineId(1, [1, 2])
      const b = buildLineId(1, [2, 1])
      expect(a).toBe(b)
    })
  })

  // -------------------------------------------------------------------------
  // addItem — consolidación
  // -------------------------------------------------------------------------

  describe('addItem', () => {
    it('consolida mismo producto sin personalización (RN-CR02)', () => {
      useCartStore.getState().addItem(productoA, 1, [], [])
      useCartStore.getState().addItem(productoA, 1, [], [])

      const items = useCartStore.getState().items
      expect(items).toHaveLength(1)
      expect(items[0].cantidad).toBe(2)
      expect(items[0].ingredientesExcluidosIds).toEqual([])
    })

    it('mantiene separados mismo producto con distintas exclusiones (RN-CR02)', () => {
      useCartStore.getState().addItem(productoA, 1, [], [])
      useCartStore.getState().addItem(productoA, 1, [3], ['Queso'])

      const items = useCartStore.getState().items
      expect(items).toHaveLength(2)
    })

    it('exclusiones en distinto orden = mismo lineId (RN-CR02)', () => {
      useCartStore.getState().addItem(productoA, 1, [1, 2], ['Tomate', 'Queso'])
      useCartStore.getState().addItem(productoA, 1, [2, 1], ['Queso', 'Tomate'])

      const items = useCartStore.getState().items
      expect(items).toHaveLength(1)
      expect(items[0].cantidad).toBe(2)
    })

    it('agrega múltiples productos distintos', () => {
      useCartStore.getState().addItem(productoA, 1, [], [])
      useCartStore.getState().addItem(productoB, 2, [], [])

      expect(useCartStore.getState().items).toHaveLength(2)
    })
  })

  // -------------------------------------------------------------------------
  // removeItem
  // -------------------------------------------------------------------------

  describe('removeItem', () => {
    it('elimina el renglón por lineId', () => {
      useCartStore.getState().addItem(productoA, 1, [], [])
      const lineId = buildLineId(productoA.id, [])
      useCartStore.getState().removeItem(lineId)

      expect(useCartStore.getState().items).toHaveLength(0)
    })

    it('no lanza error con lineId inexistente', () => {
      expect(() => useCartStore.getState().removeItem('999::')).not.toThrow()
    })
  })

  // -------------------------------------------------------------------------
  // updateCantidad
  // -------------------------------------------------------------------------

  describe('updateCantidad', () => {
    it('actualiza la cantidad de un renglón', () => {
      useCartStore.getState().addItem(productoA, 1, [], [])
      const lineId = buildLineId(productoA.id, [])
      useCartStore.getState().updateCantidad(lineId, 5)

      expect(useCartStore.getState().items[0].cantidad).toBe(5)
    })

    it('cantidad 0 elimina el renglón (RN-CR03)', () => {
      useCartStore.getState().addItem(productoA, 2, [], [])
      const lineId = buildLineId(productoA.id, [])
      useCartStore.getState().updateCantidad(lineId, 0)

      expect(useCartStore.getState().items).toHaveLength(0)
    })

    it('cantidad negativa elimina el renglón', () => {
      useCartStore.getState().addItem(productoA, 2, [], [])
      const lineId = buildLineId(productoA.id, [])
      useCartStore.getState().updateCantidad(lineId, -3)

      expect(useCartStore.getState().items).toHaveLength(0)
    })
  })

  // -------------------------------------------------------------------------
  // clearCart
  // -------------------------------------------------------------------------

  describe('clearCart', () => {
    it('vacía todos los renglones', () => {
      useCartStore.getState().addItem(productoA, 2, [], [])
      useCartStore.getState().addItem(productoB, 1, [], [])
      useCartStore.getState().clearCart()

      expect(useCartStore.getState().items).toHaveLength(0)
    })
  })

  // -------------------------------------------------------------------------
  // Selectores derivados
  // -------------------------------------------------------------------------

  describe('selectTotalItems', () => {
    it('suma cantidades de todos los renglones', () => {
      useCartStore.getState().addItem(productoA, 2, [], [])
      useCartStore.getState().addItem(productoB, 3, [], [])

      expect(selectTotalItems(useCartStore.getState())).toBe(5)
    })

    it('devuelve 0 con carrito vacío', () => {
      expect(selectTotalItems(useCartStore.getState())).toBe(0)
    })
  })

  describe('selectTotalPrice', () => {
    it('suma precio * cantidad por renglón', () => {
      // productoA: 1500 * 2 = 3000, productoB: 2000 * 1 = 2000 → total 5000
      useCartStore.getState().addItem(productoA, 2, [], [])
      useCartStore.getState().addItem(productoB, 1, [], [])

      expect(selectTotalPrice(useCartStore.getState())).toBe(5000)
    })

    it('devuelve 0 con carrito vacío', () => {
      expect(selectTotalPrice(useCartStore.getState())).toBe(0)
    })
  })
})
