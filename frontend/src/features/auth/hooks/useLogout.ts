import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { authApi } from '@/api/endpoints/auth'
import { useAuthStore } from '@/store/authStore'

export function useLogout() {
  const clearSession = useAuthStore((s) => s.clearSession)
  const refreshToken = useAuthStore((s) => s.refreshToken)
  const queryClient = useQueryClient()
  const navigate = useNavigate()

  return useMutation({
    mutationFn: async () => {
      if (refreshToken) {
        await authApi.logout({ refresh_token: refreshToken })
      }
    },
    onSettled: () => {
      clearSession()
      queryClient.clear()
      navigate('/login')
    },
  })
}
