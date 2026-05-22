import { useEffect } from 'react'
import { ProductCardSkeleton } from '@/components/Skeleton'
import { useUiStore } from '@/store/uiStore'
import type { GetProductosParams } from '@/api/endpoints/productos'
import { useProductos } from '../hooks/useProductos'
import { ProductoCard } from './ProductoCard'

interface CatalogoGridProps {
  params?: GetProductosParams
}

export function CatalogoGrid({ params }: CatalogoGridProps) {
  const { data, isLoading, isError, error } = useProductos(params)
  const addToast = useUiStore((s) => s.addToast)

  useEffect(() => {
    if (isError) {
      const message =
        (error as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? 'Error al cargar los productos.'
      addToast(message, 'error')
    }
  }, [isError, error, addToast])

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {Array.from({ length: 6 }).map((_, i) => (
          <ProductCardSkeleton key={i} />
        ))}
      </div>
    )
  }

  if (!data || data.items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-text-secondary">
        <p className="text-lg font-medium">No hay productos disponibles</p>
        <p className="text-sm mt-1">Probá con otros filtros</p>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
      {data.items.map((producto) => (
        <ProductoCard key={producto.id} producto={producto} />
      ))}
    </div>
  )
}
