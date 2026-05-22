import { useQuery } from '@tanstack/react-query'
import { productosApi } from '@/api/endpoints/productos'

export function useProducto(id: number) {
  return useQuery({
    queryKey: ['productos', id],
    queryFn: async () => {
      const res = await productosApi.getProductoById(id)
      return res.data
    },
    enabled: id > 0,
  })
}
