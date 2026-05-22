/**
 * API endpoints para Ingredientes.
 */

import { apiClient } from '@/api/client'
import type {
  IngredienteCreate,
  IngredienteRead,
  IngredienteUpdate,
  PaginatedIngredientes,
} from '@/types/ingredientes'

export interface IngredientesParams {
  page?: number
  size?: number
  es_alergeno?: boolean
}

export const ingredientesApi = {
  getIngredientes: (params?: IngredientesParams) =>
    apiClient.get<PaginatedIngredientes>('/api/v1/ingredientes/', { params }),

  getIngredienteById: (id: number) =>
    apiClient.get<IngredienteRead>(`/api/v1/ingredientes/${id}`),

  createIngrediente: (data: IngredienteCreate) =>
    apiClient.post<IngredienteRead>('/api/v1/ingredientes/', data),

  updateIngrediente: (id: number, data: IngredienteUpdate) =>
    apiClient.put<IngredienteRead>(`/api/v1/ingredientes/${id}`, data),

  deleteIngrediente: (id: number) =>
    apiClient.delete<void>(`/api/v1/ingredientes/${id}`),
}
