export interface UsuarioAdmin {
  id: number
  nombre: string
  apellido: string
  email: string
  activo: boolean
  roles: string[]
  created_at: string
}

export interface UsuariosAdminListResponse {
  items: UsuarioAdmin[]
  total: number
  page: number
  size: number
  pages: number
}

export interface AsignarRolesRequest {
  roles: string[]
}

export interface ActivarRequest {
  activo: boolean
}

export interface MetricasResumen {
  total_pedidos: number
  ventas_mes: number
  productos_activos: number
  usuarios_activos: number
}

export interface VentaItem {
  fecha: string
  total: number
}

export interface VentasSeries {
  periodo: string
  series: VentaItem[]
}

export interface ProductoTop {
  producto_id: number
  nombre: string
  unidades_vendidas: number
  total_generado: number
}

export interface ProductosTopResponse {
  items: ProductoTop[]
}

export interface PedidoPorEstado {
  estado: string
  cantidad: number
}

export interface PedidosPorEstadoResponse {
  items: PedidoPorEstado[]
}
