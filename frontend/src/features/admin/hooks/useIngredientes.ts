/**
 * Hooks TanStack Query para Ingredientes (admin).
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ingredientesApi } from '@/api/endpoints/ingredientes'
import type { IngredientesParams } from '@/api/endpoints/ingredientes'
import type { IngredienteCreate, IngredienteUpdate } from '@/types/ingredientes'

const QUERY_KEY = ['ingredientes'] as const

export function useIngredientes(params?: IngredientesParams) {
  return useQuery({
    queryKey: [...QUERY_KEY, params],
    queryFn: async () => {
      const res = await ingredientesApi.getIngredientes(params)
      return res.data
    },
  })
}

export function useCreateIngrediente() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data: IngredienteCreate) => {
      const res = await ingredientesApi.createIngrediente(data)
      return res.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY })
    },
  })
}

export function useUpdateIngrediente() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, data }: { id: number; data: IngredienteUpdate }) => {
      const res = await ingredientesApi.updateIngrediente(id, data)
      return res.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY })
    },
  })
}

export function useDeleteIngrediente() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (id: number) => {
      await ingredientesApi.deleteIngrediente(id)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY })
    },
  })
}
