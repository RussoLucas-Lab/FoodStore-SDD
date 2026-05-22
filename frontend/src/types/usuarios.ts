export interface UsuarioMeRead {
  id: number
  nombre: string
  apellido: string
  email: string
  activo: boolean
  created_at: string
}

export interface UsuarioMeUpdate {
  nombre?: string
  apellido?: string
}

export interface PasswordChangeRequest {
  password_actual: string
  password_nuevo: string
  password_nuevo_confirmar: string
}
