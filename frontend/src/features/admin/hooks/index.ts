// Admin hooks
export {
  useCategoriaTree,
  useCreateCategoria,
  useUpdateCategoria,
  useDeleteCategoria,
} from './useCategorias'
export {
  useIngredientes,
  useCreateIngrediente,
  useUpdateIngrediente,
  useDeleteIngrediente,
} from './useIngredientes'
export { useGestionPedidos } from './useGestionPedidos'
export { useAvanzarEstado } from './useAvanzarEstado'
export { useMetricasResumen } from './useMetricasResumen'
export { useVentasPorPeriodo } from './useVentasPorPeriodo'
export { useProductosTop } from './useProductosTop'
export { usePedidosPorEstado } from './usePedidosPorEstado'
export { useUsuariosAdmin } from './useUsuariosAdmin'
export {
  useUpdateUsuario,
  useAsignarRoles,
  useActivarUsuario,
} from './useAdminMutations'
