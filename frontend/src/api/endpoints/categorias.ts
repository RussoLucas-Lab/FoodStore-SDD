/**
 * API endpoints para Categorias.
 */

import { apiClient } from '@/api/client'
import type {
  CategoriaCreate,
  CategoriaRead,
  CategoriaTreeRead,
  CategoriaUpdate,
} from '@/types/categorias'

export const categoriasApi = {
  getCategorias: () =>
    apiClient.get<CategoriaTreeRead[]>('/api/v1/categorias/'),

  getCategoriaById: (id: number) =>
    apiClient.get<CategoriaRead>(`/api/v1/categorias/${id}`),

  createCategoria: (data: CategoriaCreate) =>
    apiClient.post<CategoriaRead>('/api/v1/categorias/', data),

  updateCategoria: (id: number, data: CategoriaUpdate) =>
    apiClient.put<CategoriaRead>(`/api/v1/categorias/${id}`, data),

  deleteCategoria: (id: number) =>
    apiClient.delete<void>(`/api/v1/categorias/${id}`),
}
