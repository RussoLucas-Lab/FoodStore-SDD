/**
 * API client — Axios con interceptors JWT.
 *
 * Request: agrega Authorization: Bearer <accessToken>.
 * Response: 401 ACCESS_TOKEN_EXPIRED → POST /auth/refresh → reintenta.
 *           Si el refresh falla → clearSession + toast + redirect /login.
 *           400/403/500 → toast de error global (saltea 401).
 */

import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios'
import { useAuthStore } from '@/store/authStore'
import { useUiStore } from '@/store/uiStore'

// ---------------------------------------------------------------------------
// Instancia base
// ---------------------------------------------------------------------------

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' },
  withCredentials: false,
})

// ---------------------------------------------------------------------------
// Request interceptor — adjuntar token JWT
// ---------------------------------------------------------------------------

apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = useAuthStore.getState().accessToken
    if (token && config.headers) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  (error: unknown) => Promise.reject(error),
)

// ---------------------------------------------------------------------------
// Response interceptor — 401 con refresh automático + toast de errores
// ---------------------------------------------------------------------------

let isRefreshing = false
let failedQueue: Array<{
  resolve: (token: string) => void
  reject: (error: unknown) => void
}> = []

function processQueue(error: unknown, token: string | null = null): void {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) reject(error)
    else if (token) resolve(token)
  })
  failedQueue = []
}

interface ErrorBody {
  code?: string
  detail?: string
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ErrorBody>) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean
    }

    const statusCode = error.response?.status
    const errorCode = error.response?.data?.code
    const isRefreshEndpoint = originalRequest?.url?.includes('/auth/refresh')

    // --- Refresh automático solo para ACCESS_TOKEN_EXPIRED ---
    const shouldRefresh =
      statusCode === 401 &&
      errorCode === 'ACCESS_TOKEN_EXPIRED' &&
      !originalRequest?._retry &&
      !isRefreshEndpoint

    if (shouldRefresh) {
      if (isRefreshing) {
        return new Promise<string>((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then((token) => {
          if (originalRequest.headers) {
            originalRequest.headers['Authorization'] = `Bearer ${token}`
          }
          return apiClient(originalRequest)
        })
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        const refreshToken = useAuthStore.getState().refreshToken
        if (!refreshToken) throw new Error('No refresh token')

        const response = await apiClient.post<{
          access_token: string
          refresh_token: string
        }>('/api/v1/auth/refresh', { refresh_token: refreshToken })

        const { access_token, refresh_token } = response.data
        const usuario = useAuthStore.getState().usuario

        if (usuario) {
          useAuthStore.getState().setSession(
            { access_token, refresh_token, token_type: 'bearer', expires_in: 1800 },
            usuario,
          )
        }

        processQueue(null, access_token)

        if (originalRequest.headers) {
          originalRequest.headers['Authorization'] = `Bearer ${access_token}`
        }
        return apiClient(originalRequest)
      } catch (refreshError) {
        processQueue(refreshError, null)
        useAuthStore.getState().clearSession()
        useUiStore.getState().addToast('Sesión expirada. Por favor iniciá sesión nuevamente.', 'error')
        window.location.href = '/login'
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    // --- Toast global para 400 / 403 / 500 (no para 401) ---
    if (statusCode && [400, 403, 500].includes(statusCode)) {
      const detail =
        error.response?.data?.detail ?? 'Ocurrió un error inesperado.'
      useUiStore.getState().addToast(String(detail), 'error')
    }

    return Promise.reject(error)
  },
)

export default apiClient
