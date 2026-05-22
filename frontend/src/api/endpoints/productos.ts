/**
 * API endpoints para Productos.
 */

import { apiClient } from '@/api/client'
import type {
  DisponibilidadUpdate,
  IngredienteSimple,
  ProductoCreate,
  ProductoListResponse,
  ProductoRead,
  ProductoUpdate,
  StockUpdate,
} from '@/types/productos'

export interface GetProductosParams {
  page?: number
  size?: number
  categoria_id?: number
  q?: string
  disponible?: boolean
  excluir_alergenos?: boolean
}

export const productosApi = {
  getProductos: (params?: GetProductosParams) =>
    apiClient.get<ProductoListResponse>('/api/v1/productos/', { params }),

  getProductoById: (id: number) =>
    apiClient.get<ProductoRead>(`/api/v1/productos/${id}`),

  getProductoIngredientes: (id: number) =>
    apiClient.get<IngredienteSimple[]>(`/api/v1/productos/${id}/ingredientes`),

  createProducto: (data: ProductoCreate) =>
    apiClient.post<ProductoRead>('/api/v1/productos/', data),

  updateProducto: (id: number, data: ProductoUpdate) =>
    apiClient.put<ProductoRead>(`/api/v1/productos/${id}`, data),

  patchDisponibilidad: (id: number, data: DisponibilidadUpdate) =>
    apiClient.patch<ProductoRead>(`/api/v1/productos/${id}/disponibilidad`, data),

  patchStock: (id: number, data: StockUpdate) =>
    apiClient.patch<ProductoRead>(`/api/v1/productos/${id}/stock`, data),

  deleteProducto: (id: number) =>
    apiClient.delete<void>(`/api/v1/productos/${id}`),
}
