import { useMutation } from '@tanstack/react-query'
import { authApi } from '@/api/endpoints/auth'
import { useAuthStore } from '@/store/authStore'
import type { LoginRequest } from '@/types/auth'

export function useLogin() {
  const setSession = useAuthStore((s) => s.setSession)

  return useMutation({
    mutationFn: async (body: LoginRequest) => {
      const tokensRes = await authApi.login(body)
      const tokens = tokensRes.data
      // Llamar /me con el token recién obtenido (antes de guardarlo en el store)
      const meRes = await authApi.getMe(tokens.access_token)
      return { tokens, usuario: meRes.data }
    },
    onSuccess: ({ tokens, usuario }) => {
      // Solo guarda la sesión; LoginPage maneja el redirect según rol
      setSession(tokens, usuario)
    },
  })
}
