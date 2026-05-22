/**
 * Tipos para el store del carrito de compras.
 */

export interface CartItem {
  /** Identificador derivado: `${productoId}::${sortedExcludedIds}` */
  lineId: string
  productoId: number
  nombre: string
  precio: number
  cantidad: number
  ingredientesExcluidosIds: number[]
  ingredientesExcluidosNombres: string[]
}

export interface CartState {
  items: CartItem[]
}

export interface CartActions {
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
