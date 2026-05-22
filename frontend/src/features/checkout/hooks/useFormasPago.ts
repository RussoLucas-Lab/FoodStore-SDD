import { useQuery } from '@tanstack/react-query'
import { listFormasPago } from '@/api/endpoints/formasPago'

export function useFormasPago() {
  return useQuery({
    queryKey: ['formas-pago'],
    queryFn: listFormasPago,
    staleTime: 5 * 60 * 1000,
  })
}
