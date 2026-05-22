export interface CategoriaSimple {
  id: number
  nombre: string
}

export interface IngredienteSimple {
  id: number
  nombre: string
  es_alergeno: boolean
}

export interface ProductoRead {
  id: number
  nombre: string
  descripcion: string | null
  precio_base: number
  stock_cantidad: number
  disponible: boolean
  imagen_url: string | null
  created_at: string
  deleted_at: string | null
  categorias: CategoriaSimple[]
  ingredientes: IngredienteSimple[]
}

export interface ProductoCreate {
  nombre: string
  descripcion?: string
  precio_base: number
  stock_cantidad?: number
  disponible?: boolean
  imagen_url?: string
  categoria_ids?: number[]
  ingrediente_ids?: number[]
}

export interface ProductoUpdate extends Partial<ProductoCreate> {}

export interface StockUpdate {
  cantidad: number
}

export interface DisponibilidadUpdate {
  disponible: boolean
}

export interface ProductoListResponse {
  items: ProductoRead[]
  total: number
  page: number
  size: number
  pages: number
}
