import { useQuery } from '@tanstack/react-query'
import { getMetricasResumen } from '@/api/endpoints/admin'
import type { MetricasResumen } from '@/types/admin'

export function useMetricasResumen() {
  return useQuery<MetricasResumen>({
    queryKey: ['admin', 'metricas', 'resumen'],
    queryFn: getMetricasResumen,
    staleTime: 5 * 60 * 1000,
  })
}
