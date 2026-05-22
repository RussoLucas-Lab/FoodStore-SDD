/**
 * cartStore — gestión del carrito de compras.
 *
 * Persiste items en localStorage con key `food-store:cart:v1` (RN-CR01).
 * Identifica renglones por lineId derivado (RN-CR02):
 *   lineId = `${productoId}::${[...excludedIds].sort().join(",")}`
 *
 * Convención: suscribirse por slice.
 * Ejemplo: const items = useCartStore(s => s.items)
 */

import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import type { CartItem } from '@/types/carrito'

// ---------------------------------------------------------------------------
// Helper: buildLineId — genera la clave determinista para un renglón
// ---------------------------------------------------------------------------

export function buildLineId(productoId: number, excludedIds: number[]): string {
  const sorted = [...excludedIds].sort((a, b) => a - b).join(',')
  return `${productoId}::${sorted}`
}

// ---------------------------------------------------------------------------
// Selectores derivados (pure functions — no Zustand state)
// ---------------------------------------------------------------------------

export function selectTotalItems(state: { items: CartItem[] }): number {
  return state.items.reduce((acc, item) => acc + item.cantidad, 0)
}

export function selectTotalPrice(state: { items: CartItem[] }): number {
  return state.items.reduce((acc, item) => acc + item.precio * item.cantidad, 0)
}

// ---------------------------------------------------------------------------
// Store
// ---------------------------------------------------------------------------

interface CartStore {
  items: CartItem[]
  addItem: (
    producto: { id: number; nombre: string; precio_base: number },
    cantidad: number,
    ingredientesExcluidosIds: number[],
    ingredientesExcluidosNombres: string[],
  ) => void
  removeItem: (lineId: string) => void
  updateCantidad: (lineId: string, cantidad: number) => void
  clearCart: () => void
}

export const useCartStore = create<CartStore>()(
  persist(
    (set, get) => ({
      items: [],

      addItem: (producto, cantidad, ingredientesExcluidosIds, ingredientesExcluidosNombres) => {
        const lineId = buildLineId(producto.id, ingredientesExcluidosIds)
        const existing = get().items.find((i) => i.lineId === lineId)

        if (existing) {
          // RN-CR02: mismo lineId → consolidar sumando cantidad
          set({
            items: get().items.map((i) =>
              i.lineId === lineId ? { ...i, cantidad: i.cantidad + cantidad } : i,
            ),
          })
        } else {
          const newItem: CartItem = {
            lineId,
            productoId: producto.id,
            nombre: producto.nombre,
            precio: producto.precio_base,
            cantidad,
            ingredientesExcluidosIds: [...ingredientesExcluidosIds].sort((a, b) => a - b),
            ingredientesExcluidosNombres,
          }
          set({ items: [...get().items, newItem] })
        }
      },

      removeItem: (lineId) => {
        set({ items: get().items.filter((i) => i.lineId !== lineId) })
      },

      updateCantidad: (lineId, cantidad) => {
        if (cantidad <= 0) {
          get().removeItem(lineId)
          return
        }
        set({
          items: get().items.map((i) => (i.lineId === lineId ? { ...i, cantidad } : i)),
        })
      },

      clearCart: () => set({ items: [] }),
    }),
    {
      name: 'food-store:cart:v1',
      storage: createJSONStorage(() => localStorage),
      // Solo persistir items; selectores derivados se recomputan en cada render
      partialize: (state) => ({ items: state.items }),
    },
  ),
)
