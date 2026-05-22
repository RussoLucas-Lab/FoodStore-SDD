import { useQuery } from '@tanstack/react-query'
import { getUsuariosAdmin, type GetUsuariosAdminParams } from '@/api/endpoints/admin'
import type { UsuariosAdminListResponse } from '@/types/admin'

export function useUsuariosAdmin(params?: GetUsuariosAdminParams) {
  return useQuery<UsuariosAdminListResponse>({
    queryKey: ['admin', 'usuarios', params ?? {}],
    queryFn: () => getUsuariosAdmin(params),
  })
}
