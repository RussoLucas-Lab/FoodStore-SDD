import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { usuariosApi } from '@/api/endpoints/usuarios'
import type { PasswordChangeRequest, UsuarioMeUpdate } from '@/types/usuarios'

const ME_KEY = ['me'] as const

export function useMe() {
  return useQuery({
    queryKey: ME_KEY,
    queryFn: async () => {
      const res = await usuariosApi.getMe()
      return res.data
    },
  })
}

export function useUpdateMe() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data: UsuarioMeUpdate) => {
      const res = await usuariosApi.updateMe(data)
      return res.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ME_KEY })
    },
  })
}

export function useChangePassword() {
  return useMutation({
    mutationFn: async (data: PasswordChangeRequest) => {
      await usuariosApi.changePassword(data)
    },
  })
}
