/**
 * authStore — gestión de sesión del usuario.
 *
 * Persiste accessToken y refreshToken en localStorage.
 * El objeto usuario se reconstruye con GET /api/v1/auth/me al recargar.
 *
 * Suscribirse por slice: const token = useAuthStore(s => s.accessToken)
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Rol, TokenResponse, UserPublic } from '@/types/auth'

interface AuthState {
  accessToken: string | null
  refreshToken: string | null
  usuario: UserPublic | null
  readonly isAuthenticated: boolean

  setSession: (tokens: TokenResponse, usuario: UserPublic) => void
  setUsuario: (usuario: UserPublic) => void
  clearSession: () => void
  hasRole: (role: Rol) => boolean
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      accessToken: null,
      refreshToken: null,
      usuario: null,

      get isAuthenticated() {
        return get().accessToken !== null
      },

      setSession: (tokens, usuario) =>
        set({
          accessToken: tokens.access_token,
          refreshToken: tokens.refresh_token,
          usuario,
        }),

      setUsuario: (usuario) => set({ usuario }),

      clearSession: () =>
        set({ accessToken: null, refreshToken: null, usuario: null }),

      hasRole: (role) => get().usuario?.rol === role,
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
      }),
    },
  ),
)

// Selectores tipados por slice
export const useAccessToken = () => useAuthStore((s) => s.accessToken)
export const useRefreshToken = () => useAuthStore((s) => s.refreshToken)
export const useUsuario = () => useAuthStore((s) => s.usuario)
export const useIsAuthenticated = () =>
  useAuthStore((s) => s.accessToken !== null)
