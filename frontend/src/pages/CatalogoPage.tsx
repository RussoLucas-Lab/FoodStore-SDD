import { useState } from 'react'
import { CatalogoGrid } from '@/features/catalogo/components/CatalogoGrid'
import { FiltrosBarra } from '@/features/catalogo/components/FiltrosBarra'
import { Paginacion } from '@/features/catalogo/components/Paginacion'
import { useProductos } from '@/features/catalogo/hooks/useProductos'
import type { FiltrosState } from '@/features/catalogo/components/FiltrosBarra'

const PAGE_SIZE = 12

export default function CatalogoPage() {
  const [filtros, setFiltros] = useState<FiltrosState>({
    categoriaId: undefined,
    q: '',
  })
  const [page, setPage] = useState(1)

  const params = {
    page,
    size: PAGE_SIZE,
    categoria_id: filtros.categoriaId,
    q: filtros.q || undefined,
    disponible: true,
  }

  const { data } = useProductos(params)

  const handleFiltrosChange = (newFiltros: FiltrosState) => {
    setFiltros(newFiltros)
    setPage(1) // Reset to first page on filter change
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-text-primary mb-4">Catálogo</h1>
        <FiltrosBarra value={filtros} onChange={handleFiltrosChange} />
      </div>

      <CatalogoGrid params={params} />

      {data && (
        <Paginacion
          page={data.page}
          size={data.size}
          total={data.total}
          pages={data.pages}
          onPageChange={setPage}
        />
      )}
    </div>
  )
}
