import { useQuery } from '@tanstack/react-query'
import { getProductosTop } from '@/api/endpoints/admin'
import type { ProductosTopResponse } from '@/types/admin'

export function useProductosTop(limit: number = 10) {
  return useQuery<ProductosTopResponse>({
    queryKey: ['admin', 'metricas', 'productos-top', limit],
    queryFn: () => getProductosTop(limit),
    staleTime: 5 * 60 * 1000,
  })
}
