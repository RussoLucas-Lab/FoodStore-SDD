/**
 * PedidosList — listado paginado de pedidos del usuario autenticado.
 *
 * Características:
 *   - Skeleton loaders mientras carga
 *   - Estado vacío con CTA al catálogo
 *   - Controles de paginación (prev / next)
 */

import { useState } from 'react'
import { Link } from 'react-router-dom'
import { usePedidos } from '../hooks/usePedidos'
import { PedidoCard } from './PedidoCard'
import { Skeleton } from '@/components/Skeleton'
import { Button } from '@/components/Button'

const PAGE_SIZE = 10

export function PedidosList() {
  const [page, setPage] = useState(1)
  const { data, isLoading, isError } = usePedidos({ page, size: PAGE_SIZE })

  if (isLoading) {
    return (
      <div className="grid gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="bg-white border border-border-color rounded-md p-4">
            <div className="flex justify-between mb-3">
              <Skeleton className="h-4 w-28" />
              <Skeleton className="h-5 w-20 rounded-full" />
            </div>
            <Skeleton className="h-6 w-24" />
          </div>
        ))}
      </div>
    )
  }

  if (isError) {
    return (
      <p className="text-error text-sm">
        No se pudieron cargar los pedidos. Intentá nuevamente.
      </p>
    )
  }

  if (!data || data.items.length === 0) {
    return (
      <div className="text-center py-16">
        <p className="text-text-secondary mb-4">Todavía no realizaste ningún pedido.</p>
        <Link to="/catalogo">
          <Button variant="primary">Ver catálogo</Button>
        </Link>
      </div>
    )
  }

  const totalPages = data.pages

  return (
    <div>
      <div className="grid gap-4">
        {data.items.map((pedido) => (
          <PedidoCard key={pedido.id} pedido={pedido} />
        ))}
      </div>

      {/* Paginación */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between mt-6">
          <Button
            variant="secondary"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
          >
            ← Anterior
          </Button>
          <span className="text-sm text-text-secondary">
            Página {page} de {totalPages}
          </span>
          <Button
            variant="secondary"
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
          >
            Siguiente →
          </Button>
        </div>
      )}
    </div>
  )
}
