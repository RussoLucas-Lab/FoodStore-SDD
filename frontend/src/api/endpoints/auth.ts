import { apiClient } from '@/api/client'
import type {
  LoginRequest,
  RegisterRequest,
  TokenResponse,
  UserPublic,
} from '@/types/auth'

export const authApi = {
  login: (body: LoginRequest) =>
    apiClient.post<TokenResponse>('/api/v1/auth/login', body),

  register: (body: RegisterRequest) =>
    apiClient.post<UserPublic>('/api/v1/auth/register', body),

  refresh: (body: { refresh_token: string }) =>
    apiClient.post<TokenResponse>('/api/v1/auth/refresh', body),

  logout: (body: { refresh_token: string }) =>
    apiClient.post<void>('/api/v1/auth/logout', body),

  getMe: (token?: string) =>
    apiClient.get<UserPublic>('/api/v1/auth/me', {
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    }),
}
