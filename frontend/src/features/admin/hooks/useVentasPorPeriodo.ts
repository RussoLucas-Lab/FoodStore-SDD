import { useQuery } from '@tanstack/react-query'
import { getVentasPorPeriodo } from '@/api/endpoints/admin'
import type { VentasSeries } from '@/types/admin'

export type Periodo = 'dia' | 'semana' | 'mes'

export function useVentasPorPeriodo(periodo: Periodo = 'mes') {
  return useQuery<VentasSeries>({
    queryKey: ['admin', 'metricas', 'ventas', periodo],
    queryFn: () => getVentasPorPeriodo(periodo),
    staleTime: 5 * 60 * 1000,
  })
}
