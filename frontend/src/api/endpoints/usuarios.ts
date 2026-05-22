/**
 * API endpoints para Usuarios (perfil propio).
 */

import { apiClient } from '@/api/client'
import type {
  PasswordChangeRequest,
  UsuarioMeRead,
  UsuarioMeUpdate,
} from '@/types/usuarios'

export const usuariosApi = {
  getMe: () => apiClient.get<UsuarioMeRead>('/api/v1/usuarios/me'),

  updateMe: (data: UsuarioMeUpdate) =>
    apiClient.put<UsuarioMeRead>('/api/v1/usuarios/me', data),

  changePassword: (data: PasswordChangeRequest) =>
    apiClient.patch<void>('/api/v1/usuarios/me/password', data),
}
