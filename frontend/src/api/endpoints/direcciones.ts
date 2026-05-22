/**
 * API endpoints para Direcciones de entrega.
 */

import { apiClient } from '@/api/client'
import type { DireccionCreate, DireccionRead, DireccionUpdate } from '@/types/direcciones'

interface SetPrincipalResponse {
  message: string
  direccion: DireccionRead
}

export const direccionesApi = {
  getDirecciones: () =>
    apiClient.get<DireccionRead[]>('/api/v1/direcciones/'),

  createDireccion: (data: DireccionCreate) =>
    apiClient.post<DireccionRead>('/api/v1/direcciones/', data),

  updateDireccion: (id: number, data: DireccionUpdate) =>
    apiClient.put<DireccionRead>(`/api/v1/direcciones/${id}`, data),

  setPrincipal: (id: number) =>
    apiClient.patch<SetPrincipalResponse>(`/api/v1/direcciones/${id}/principal`),

  deleteDireccion: (id: number) =>
    apiClient.delete<void>(`/api/v1/direcciones/${id}`),
}
