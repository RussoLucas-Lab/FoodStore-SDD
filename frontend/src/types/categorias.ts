/**
 * Tipos TypeScript para el módulo de Categorías.
 */

export interface CategoriaRead {
  id: number
  nombre: string
  parent_id: number | null
  descripcion: string | null
  orden: number
  activa: boolean
  deleted_at: string | null
}

export interface CategoriaTreeRead {
  id: number
  nombre: string
  parent_id: number | null
  descripcion: string | null
  orden: number
  activa: boolean
  subcategorias: CategoriaTreeRead[]
}

export interface CategoriaCreate {
  nombre: string
  parent_id?: number | null
  descripcion?: string | null
  orden?: number
}

export interface CategoriaUpdate {
  nombre?: string
  parent_id?: number | null
  descripcion?: string | null
  orden?: number
  activa?: boolean
}
