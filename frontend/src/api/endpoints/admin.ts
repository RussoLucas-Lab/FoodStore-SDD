import { apiClient } from '@/api/client'
import type {
  ActivarRequest,
  AsignarRolesRequest,
  MetricasResumen,
  PedidosPorEstadoResponse,
  ProductosTopResponse,
  UsuarioAdmin,
  UsuariosAdminListResponse,
  VentasSeries,
} from '@/types/admin'

const BASE = '/api/v1/admin'

export interface GetUsuariosAdminParams {
  q?: string
  activo?: boolean
  page?: number
  size?: number
}

export function getUsuariosAdmin(
  params?: GetUsuariosAdminParams,
): Promise<UsuariosAdminListResponse> {
  return apiClient.get(`${BASE}/usuarios`, { params }).then((r) => r.data)
}

export function updateUsuarioAdmin(
  id: number,
  data: Partial<Pick<UsuarioAdmin, 'nombre' | 'apellido' | 'email'>>,
): Promise<UsuarioAdmin> {
  return apiClient.put(`${BASE}/usuarios/${id}`, data).then((r) => r.data)
}

export function asignarRoles(
  id: number,
  data: AsignarRolesRequest,
): Promise<UsuarioAdmin> {
  return apiClient.patch(`${BASE}/usuarios/${id}/roles`, data).then((r) => r.data)
}

export function activarUsuario(
  id: number,
  data: ActivarRequest,
): Promise<UsuarioAdmin> {
  return apiClient.patch(`${BASE}/usuarios/${id}/activar`, data).then((r) => r.data)
}

export function getMetricasResumen(): Promise<MetricasResumen> {
  return apiClient.get(`${BASE}/metricas/resumen`).then((r) => r.data)
}

export function getVentasPorPeriodo(
  periodo: 'dia' | 'semana' | 'mes',
): Promise<VentasSeries> {
  return apiClient.get(`${BASE}/metricas/ventas`, { params: { periodo } }).then((r) => r.data)
}

export function getProductosTop(limit?: number): Promise<ProductosTopResponse> {
  return apiClient
    .get(`${BASE}/metricas/productos-top`, { params: { limit } })
    .then((r) => r.data)
}

export function getPedidosPorEstado(): Promise<PedidosPorEstadoResponse> {
  return apiClient.get(`${BASE}/metricas/pedidos-por-estado`).then((r) => r.data)
}
