/**
 * HistorialTimeline — timeline vertical del historial de estados de un pedido.
 *
 * Cada nodo muestra:
 *   - Estado anterior → estado actual
 *   - Fecha y hora del cambio
 *   - Actor (ID del usuario que realizó el cambio)
 *   - Motivo (si existe)
 *
 * El último nodo (estado actual) se destaca visualmente.
 */

import type { HistorialEstadoRead } from '@/types/pedidos'

interface HistorialTimelineProps {
  historial: HistorialEstadoRead[]
}

const ESTADO_LABELS: Record<string, string> = {
  PENDIENTE: 'Pendiente',
  CONFIRMADO: 'Confirmado',
  EN_PREP: 'En preparación',
  EN_CAMINO: 'En camino',
  ENTREGADO: 'Entregado',
  CANCELADO: 'Cancelado',
}

function formatFecha(iso: string): string {
  return new Date(iso).toLocaleString('es-AR', {
    dateStyle: 'medium',
    timeStyle: 'short',
  })
}

export function HistorialTimeline({ historial }: HistorialTimelineProps) {
  if (historial.length === 0) {
    return (
      <p className="text-sm text-text-secondary">Sin registros de historial.</p>
    )
  }

  return (
    <ol className="relative border-l border-border-color ml-3">
      {historial.map((nodo, idx) => {
        const isLast = idx === historial.length - 1
        const label = ESTADO_LABELS[nodo.estado_hasta] ?? nodo.estado_hasta

        return (
          <li key={nodo.id} className="mb-6 ml-6">
            {/* Punto en la línea */}
            <span
              className={`absolute -left-3 flex h-6 w-6 items-center justify-center rounded-full ring-4 ring-white ${
                isLast ? 'bg-blue-500' : 'bg-gray-200'
              }`}
            >
              {isLast ? (
                <svg
                  className="h-3 w-3 text-white"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                  aria-hidden="true"
                >
                  <circle cx="10" cy="10" r="6" />
                </svg>
              ) : (
                <svg
                  className="h-3 w-3 text-gray-400"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                  aria-hidden="true"
                >
                  <circle cx="10" cy="10" r="4" />
                </svg>
              )}
            </span>

            {/* Contenido del nodo */}
            <div
              className={`rounded-md p-3 ${
                isLast ? 'bg-blue-50 border border-blue-200' : 'bg-surface'
              }`}
            >
              <p className={`text-sm font-medium ${isLast ? 'text-blue-800' : 'text-text-primary'}`}>
                {nodo.estado_desde ? (
                  <>
                    {ESTADO_LABELS[nodo.estado_desde] ?? nodo.estado_desde}
                    {' → '}
                    {label}
                  </>
                ) : (
                  <>Pedido creado — {label}</>
                )}
              </p>

              <time className="text-xs text-text-secondary block mt-1">
                {formatFecha(nodo.created_at)}
              </time>

              {nodo.motivo && (
                <p className="text-xs text-text-secondary mt-1 italic">
                  Motivo: {nodo.motivo}
                </p>
              )}
            </div>
          </li>
        )
      })}
    </ol>
  )
}
