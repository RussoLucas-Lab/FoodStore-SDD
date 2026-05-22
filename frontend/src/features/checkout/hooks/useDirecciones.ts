/**
 * Hooks TanStack Query para el módulo de direcciones.
 *
 * D10: Direcciones = estado del servidor → TanStack Query (no Zustand).
 * Todas las mutations invalidan ['direcciones'] en onSuccess.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import type { AxiosError } from 'axios'
import { direccionesApi } from '@/api/endpoints/direcciones'
import { useUiStore } from '@/store/uiStore'
import type { DireccionCreate, DireccionRead, DireccionUpdate } from '@/types/direcciones'

const DIRECCIONES_KEY = ['direcciones'] as const

// ---------------------------------------------------------------------------
// Query
// ---------------------------------------------------------------------------

export function useDirecciones() {
  return useQuery({
    queryKey: DIRECCIONES_KEY,
    queryFn: async () => {
      const res = await direccionesApi.getDirecciones()
      return res.data
    },
  })
}

// ---------------------------------------------------------------------------
// Helper para toast de error desde el backend
// ---------------------------------------------------------------------------

function useErrorToast() {
  const addToast = useUiStore((s) => s.addToast)
  return (error: unknown) => {
    const axiosErr = error as AxiosError<{ detail?: string }>
    const detail = axiosErr.response?.data?.detail ?? 'Ocurrió un error inesperado.'
    addToast(String(detail), 'error')
  }
}

// ---------------------------------------------------------------------------
// Mutations
// ---------------------------------------------------------------------------

export function useCreateDireccion() {
  const queryClient = useQueryClient()
  const addToast = useUiStore((s) => s.addToast)
  const onError = useErrorToast()

  return useMutation({
    mutationFn: async (data: DireccionCreate) => {
      const res = await direccionesApi.createDireccion(data)
      return res.data as DireccionRead
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: DIRECCIONES_KEY })
      addToast('Dirección creada.', 'success')
    },
    onError,
  })
}

export function useUpdateDireccion() {
  const queryClient = useQueryClient()
  const addToast = useUiStore((s) => s.addToast)
  const onError = useErrorToast()

  return useMutation({
    mutationFn: async ({ id, data }: { id: number; data: DireccionUpdate }) => {
      const res = await direccionesApi.updateDireccion(id, data)
      return res.data as DireccionRead
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: DIRECCIONES_KEY })
      addToast('Dirección actualizada.', 'success')
    },
    onError,
  })
}

export function useSetPrincipal() {
  const queryClient = useQueryClient()
  const addToast = useUiStore((s) => s.addToast)
  const onError = useErrorToast()

  return useMutation({
    mutationFn: async (id: number) => {
      const res = await direccionesApi.setPrincipal(id)
      return res.data
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: DIRECCIONES_KEY })
      addToast('Dirección principal actualizada.', 'success')
    },
    onError,
  })
}

export function useDeleteDireccion() {
  const queryClient = useQueryClient()
  const addToast = useUiStore((s) => s.addToast)
  const onError = useErrorToast()

  return useMutation({
    mutationFn: async (id: number) => {
      await direccionesApi.deleteDireccion(id)
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: DIRECCIONES_KEY })
      addToast('Dirección eliminada.', 'success')
    },
    onError,
  })
}
