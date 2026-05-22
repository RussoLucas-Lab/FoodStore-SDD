/**
 * GestionPedidosTable — tabla de gestión de pedidos para roles ADMIN/PEDIDOS.
 *
 * Características:
 *   - Tabla paginada con columnas: id, fecha, estado, total, acción
 *   - Chips de filtro por cada estado FSM
 *   - Búsqueda por id de pedido
 *   - Botón "Avanzar" deshabilitado en estados terminales
 *   - Usa AvanzarEstadoModal para confirmación
 */

import { useState } from 'react'
import { useGestionPedidos } from '../hooks/useGestionPedidos'
import { AvanzarEstadoModal } from './AvanzarEstadoModal'
import { EstadoPedidoBadge } from '@/features/pedidos/components/EstadoPedidoBadge'
import { Button } from '@/components/Button'
import { Skeleton } from '@/components/Skeleton'
import type { PedidoRead } from '@/types/pedidos'

const PAGE_SIZE = 15

const ESTADOS_FSM = [
  'PENDIENTE',
  'CONFIRMADO',
  'EN_PREP',
  'EN_CAMINO',
  'ENTREGADO',
  'CANCELADO',
] as const

const TERMINAL_STATES = new Set(['ENTREGADO', 'CANCELADO'])

// Mapa de transiciones para determinar el siguiente estado
const NEXT_STATE: Record<string, string> = {
  CONFIRMADO: 'EN_PREP',
  EN_PREP: 'EN_CAMINO',
  EN_CAMINO: 'ENTREGADO',
}

function formatFecha(iso: string): string {
  return new Date(iso).toLocaleDateString('es-AR', { dateStyle: 'short' })
}

function formatMoneda(value: number): string {
  return new Intl.NumberFormat('es-AR', {
    style: 'currency',
    currency: 'ARS',
  }).format(value)
}

export function GestionPedidosTable() {
  const [page, setPage] = useState(1)
  const [estadoFiltro, setEstadoFiltro] = useState<string | undefined>(undefined)
  const [searchId, setSearchId] = useState('')

  const [selectedPedido, setSelectedPedido] = useState<PedidoRead | null>(null)
  const [showModal, setShowModal] = useState(false)

  const { data, isLoading, isError } = useGestionPedidos({
    page,
    size: PAGE_SIZE,
    estado_codigo: estadoFiltro,
  })

  function handleEstadoFiltro(estado: string | undefined) {
    setEstadoFiltro(estado)
    setPage(1)
  }

  function handleAvanzar(pedido: PedidoRead) {
    setSelectedPedido(pedido)
    setShowModal(true)
  }

  // Filtrar por id en cliente (complementa el filtro de estado del backend)
  const pedidosFiltrados = data?.items.filter((p) => {
    if (!searchId.trim()) return true
    return String(p.id).includes(searchId.trim())
  }) ?? []

  return (
    <div>
      {/* Filtros de estado */}
      <div className="flex flex-wrap gap-2 mb-4">
        <button
          onClick={() => handleEstadoFiltro(undefined)}
          className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors ${
            estadoFiltro === undefined
              ? 'bg-blue text-white border-blue'
              : 'bg-white text-text-secondary border-border-color hover:bg-surface'
          }`}
        >
          Todos
        </button>
        {ESTADOS_FSM.map((estado) => (
          <button
            key={estado}
            onClick={() => handleEstadoFiltro(estado)}
            className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors ${
              estadoFiltro === estado
                ? 'ring-2 ring-offset-1 ring-blue'
                : 'bg-white border-border-color hover:bg-surface'
            }`}
          >
            <EstadoPedidoBadge estado={estado} />
          </button>
        ))}
      </div>

      {/* Búsqueda por id */}
      <div className="mb-4">
        <input
          type="text"
          value={searchId}
          onChange={(e) => setSearchId(e.target.value)}
          placeholder="Buscar por ID de pedido..."
          className="border border-border-color rounded-md px-3 py-2 text-sm w-64 focus:outline-none focus:ring-2 focus:ring-blue"
        />
      </div>

      {/* Tabla */}
      {isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-10 w-full" />
          ))}
        </div>
      ) : isError ? (
        <p className="text-error text-sm">Error al cargar los pedidos.</p>
      ) : pedidosFiltrados.length === 0 ? (
        <p className="text-text-secondary text-sm py-8 text-center">
          No hay pedidos con los filtros seleccionados.
        </p>
      ) : (
        <div className="overflow-x-auto rounded-md border border-border-color">
          <table className="w-full text-sm">
            <thead className="bg-surface text-text-secondary text-left">
              <tr>
                <th className="px-4 py-3 font-medium">ID</th>
                <th className="px-4 py-3 font-medium">Fecha</th>
                <th className="px-4 py-3 font-medium">Estado</th>
                <th className="px-4 py-3 font-medium">Total</th>
                <th className="px-4 py-3 font-medium">Acción</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-color bg-white">
              {pedidosFiltrados.map((pedido) => {
                const isTerminal = TERMINAL_STATES.has(pedido.estado_codigo)
                const nextState = NEXT_STATE[pedido.estado_codigo]
                const canAdvance = !isTerminal && nextState !== undefined

                return (
                  <tr key={pedido.id} className="hover:bg-surface/60 transition-colors">
                    <td className="px-4 py-3 font-mono text-xs text-text-secondary">
                      #{pedido.id}
                    </td>
                    <td className="px-4 py-3 text-text-secondary">
                      {formatFecha(pedido.created_at)}
                    </td>
                    <td className="px-4 py-3">
                      <EstadoPedidoBadge estado={pedido.estado_codigo} />
                    </td>
                    <td className="px-4 py-3 font-semibold text-text-primary">
                      {formatMoneda(pedido.total)}
                    </td>
                    <td className="px-4 py-3">
                      <Button
                        variant="secondary"
                        onClick={() => handleAvanzar(pedido)}
                        disabled={!canAdvance}
                        className="text-xs py-1 px-3"
                      >
                        Avanzar
                      </Button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Paginación */}
      {data && data.pages > 1 && (
        <div className="flex items-center justify-between mt-4">
          <Button
            variant="secondary"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
          >
            ← Anterior
          </Button>
          <span className="text-sm text-text-secondary">
            Página {page} de {data.pages}
          </span>
          <Button
            variant="secondary"
            onClick={() => setPage((p) => Math.min(data.pages, p + 1))}
            disabled={page === data.pages}
          >
            Siguiente →
          </Button>
        </div>
      )}

      {/* Modal de avance */}
      {selectedPedido && NEXT_STATE[selectedPedido.estado_codigo] && (
        <AvanzarEstadoModal
          open={showModal}
          onClose={() => setShowModal(false)}
          pedidoId={selectedPedido.id}
          estadoActual={selectedPedido.estado_codigo}
          siguienteEstado={NEXT_STATE[selectedPedido.estado_codigo]}
          onSuccess={() => setSelectedPedido(null)}
        />
      )}
    </div>
  )
}
