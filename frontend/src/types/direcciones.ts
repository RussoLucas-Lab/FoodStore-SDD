/**
 * Tipos para el módulo de direcciones de entrega.
 */

export interface DireccionRead {
  id: number
  usuario_id: number
  calle: string
  numero: string
  piso: string | null
  depto: string | null
  ciudad: string
  provincia: string
  codigo_postal: string
  referencia: string | null
  es_principal: boolean
  created_at: string
  deleted_at: string | null
}

export interface DireccionCreate {
  calle: string
  numero: string
  piso?: string
  depto?: string
  ciudad: string
  provincia: string
  codigo_postal: string
  referencia?: string
  es_principal?: boolean
}

export interface DireccionUpdate {
  calle?: string
  numero?: string
  piso?: string
  depto?: string
  ciudad?: string
  provincia?: string
  codigo_postal?: string
  referencia?: string
}
