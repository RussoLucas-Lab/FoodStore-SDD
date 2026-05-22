import { useMutation, useQueryClient } from '@tanstack/react-query'
import {
  activarUsuario,
  asignarRoles,
  updateUsuarioAdmin,
} from '@/api/endpoints/admin'
import type { UsuarioAdmin } from '@/types/admin'

function invalidateUsuarios(qc: ReturnType<typeof useQueryClient>) {
  qc.invalidateQueries({ queryKey: ['admin', 'usuarios'] })
}

export function useUpdateUsuario() {
  const qc = useQueryClient()
  return useMutation<
    UsuarioAdmin,
    Error,
    { id: number; data: Partial<Pick<UsuarioAdmin, 'nombre' | 'apellido' | 'email'>> }
  >({
    mutationFn: ({ id, data }) => updateUsuarioAdmin(id, data),
    onSuccess: () => invalidateUsuarios(qc),
  })
}

export function useAsignarRoles() {
  const qc = useQueryClient()
  return useMutation<UsuarioAdmin, Error, { id: number; roles: string[] }>({
    mutationFn: ({ id, roles }) => asignarRoles(id, { roles }),
    onSuccess: () => invalidateUsuarios(qc),
  })
}

export function useActivarUsuario() {
  const qc = useQueryClient()
  return useMutation<UsuarioAdmin, Error, { id: number; activo: boolean }>({
    mutationFn: ({ id, activo }) => activarUsuario(id, { activo }),
    onSuccess: () => invalidateUsuarios(qc),
  })
}
