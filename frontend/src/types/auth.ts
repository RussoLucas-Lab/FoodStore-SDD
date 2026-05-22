export type Rol = 'ADMIN' | 'STOCK' | 'PEDIDOS' | 'CLIENT'

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
  nombre: string
  apellido: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: 'bearer'
  expires_in: number
}

export interface UserPublic {
  id: number
  email: string
  nombre: string
  apellido: string
  rol: Rol
  fecha_alta: string
}
