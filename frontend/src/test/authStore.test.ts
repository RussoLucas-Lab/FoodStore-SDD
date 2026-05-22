import { describe, it, expect, beforeEach } from 'vitest'
import { useAuthStore } from '@/store/authStore'
import type { TokenResponse, UserPublic } from '@/types/auth'

const mockTokens: TokenResponse = {
  access_token: 'fake-access-token',
  refresh_token: 'fake-refresh-token',
  token_type: 'bearer',
  expires_in: 1800,
}

const mockUsuario: UserPublic = {
  id: 1,
  email: 'test@example.com',
  nombre: 'Test',
  apellido: 'User',
  rol: 'CLIENT',
  fecha_alta: '2026-01-01T00:00:00Z',
}

describe('authStore', () => {
  beforeEach(() => {
    useAuthStore.getState().clearSession()
  })

  it('setSession popula tokens y usuario', () => {
    useAuthStore.getState().setSession(mockTokens, mockUsuario)

    const state = useAuthStore.getState()
    expect(state.accessToken).toBe('fake-access-token')
    expect(state.refreshToken).toBe('fake-refresh-token')
    expect(state.usuario).toEqual(mockUsuario)
  })

  it('isAuthenticated es true cuando hay accessToken', () => {
    useAuthStore.getState().setSession(mockTokens, mockUsuario)
    expect(useAuthStore.getState().accessToken).not.toBeNull()
  })

  it('clearSession limpia todos los campos', () => {
    useAuthStore.getState().setSession(mockTokens, mockUsuario)
    useAuthStore.getState().clearSession()

    const state = useAuthStore.getState()
    expect(state.accessToken).toBeNull()
    expect(state.refreshToken).toBeNull()
    expect(state.usuario).toBeNull()
  })

  it('hasRole retorna true si el rol coincide', () => {
    useAuthStore.getState().setSession(mockTokens, mockUsuario)
    expect(useAuthStore.getState().hasRole('CLIENT')).toBe(true)
    expect(useAuthStore.getState().hasRole('ADMIN')).toBe(false)
  })
})
