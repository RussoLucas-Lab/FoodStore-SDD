import { useMutation } from '@tanstack/react-query'
import { authApi } from '@/api/endpoints/auth'
import { useAuthStore } from '@/store/authStore'
import type { RegisterRequest } from '@/types/auth'

export function useRegister() {
  const setSession = useAuthStore((s) => s.setSession)

  return useMutation({
    mutationFn: async (body: RegisterRequest) => {
      await authApi.register(body)
      // Login automático post-registro
      const tokensRes = await authApi.login({
        email: body.email,
        password: body.password,
      })
      const tokens = tokensRes.data
      // Llamar /me con el token recién obtenido (antes de guardarlo en el store)
      const meRes = await authApi.getMe(tokens.access_token)
      return { tokens, usuario: meRes.data }
    },
    onSuccess: ({ tokens, usuario }) => {
      setSession(tokens, usuario)
    },
  })
}
