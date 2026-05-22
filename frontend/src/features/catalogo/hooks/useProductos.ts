import { useQuery } from '@tanstack/react-query'
import { productosApi } from '@/api/endpoints/productos'
import type { GetProductosParams } from '@/api/endpoints/productos'

export function useProductos(params?: GetProductosParams) {
  return useQuery({
    queryKey: ['productos', params],
    queryFn: async () => {
      const res = await productosApi.getProductos(params)
      return res.data
    },
  })
}
