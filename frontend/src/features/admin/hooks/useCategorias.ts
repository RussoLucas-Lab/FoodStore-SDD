/**
 * Hooks TanStack Query para Categorias (admin).
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { categoriasApi } from '@/api/endpoints/categorias'
import type { CategoriaCreate, CategoriaUpdate } from '@/types/categorias'

const QUERY_KEY = ['categorias'] as const

export function useCategoriaTree() {
  return useQuery({
    queryKey: QUERY_KEY,
    queryFn: async () => {
      const res = await categoriasApi.getCategorias()
      return res.data
    },
  })
}

export function useCreateCategoria() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data: CategoriaCreate) => {
      const res = await categoriasApi.createCategoria(data)
      return res.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY })
    },
  })
}

export function useUpdateCategoria() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, data }: { id: number; data: CategoriaUpdate }) => {
      const res = await categoriasApi.updateCategoria(id, data)
      return res.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY })
    },
  })
}

export function useDeleteCategoria() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (id: number) => {
      await categoriasApi.deleteCategoria(id)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY })
    },
  })
}
