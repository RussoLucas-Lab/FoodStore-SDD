/**
 * Tipos TypeScript para el módulo de Ingredientes.
 */

export interface IngredienteRead {
  id: number
  nombre: string
  es_alergeno: boolean
  deleted_at: string | null
}

export interface IngredienteCreate {
  nombre: string
  es_alergeno?: boolean
}

export interface IngredienteUpdate {
  nombre?: string
  es_alergeno?: boolean
}

export interface PaginatedIngredientes {
  items: IngredienteRead[]
  total: number
  page: number
  size: number
  pages: number
}
