import { useQuery } from '@tanstack/react-query'
import { authApi } from '@/api/endpoints/auth'
import { useAuthStore } from '@/store/authStore'

export function useCurrentUser() {
  const accessToken = useAuthStore((s) => s.accessToken)
  const setUsuario = useAuthStore((s) => s.setUsuario)

  return useQuery({
    queryKey: ['auth', 'me'],
    queryFn: async () => {
      const res = await authApi.getMe()
      setUsuario(res.data)
      return res.data
    },
    enabled: !!accessToken,
    staleTime: 1000 * 60 * 5, // 5 min
    retry: false,
  })
}
