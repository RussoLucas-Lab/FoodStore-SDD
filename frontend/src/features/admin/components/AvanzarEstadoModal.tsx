/**
 * AvanzarEstadoModal — modal de confirmación para avanzar el estado de un pedido.
 *
 * Muestra la transición "estado_actual → siguiente_estado".
 * Sin campo de motivo (solo admin/gestor avanzan, no cancelan con este modal).
 */

import type { AxiosError } from 'axios'
import { Modal } from '@/components/Modal'
import { Button } from '@/components/Button'
import { useAvanzarEstado } from '../hooks/useAvanzarEstado'
import { EstadoPedidoBadge } from '@/features/pedidos/components/EstadoPedidoBadge'

interface AvanzarEstadoModalProps {
  open: boolean
  onClose: () => void
  pedidoId: number
  estadoActual: string
  siguienteEstado: string
  onSuccess?: () => void
}

export function AvanzarEstadoModal({
  open,
  onClose,
  pedidoId,
  estadoActual,
  siguienteEstado,
  onSuccess,
}: AvanzarEstadoModalProps) {
  const avanzar = useAvanzarEstado()

  function handleConfirm() {
    avanzar.mutate(
      { pedidoId, nuevo_estado: siguienteEstado },
      {
        onSuccess: () => {
          onClose()
          onSuccess?.()
        },
      },
    )
  }

  const errorMsg = avanzar.error
    ? ((avanzar.error as AxiosError<{ detail?: string }>).response?.data?.detail ?? 'Error al cambiar el estado.')
    : null

  return (
    <Modal open={open} onClose={onClose} maxWidth="max-w-sm">
      <div className="p-6">
        <h2 className="text-lg font-semibold text-text-primary mb-3">
          Avanzar estado del pedido #{pedidoId}
        </h2>

        <div className="flex items-center gap-3 bg-surface rounded-md p-3 mb-5">
          <EstadoPedidoBadge estado={estadoActual} />
          <span className="text-text-secondary text-sm">→</span>
          <EstadoPedidoBadge estado={siguienteEstado} />
        </div>

        <p className="text-sm text-text-secondary mb-5">
          ¿Confirmás el cambio de estado?
        </p>

        {errorMsg && (
          <p className="text-sm text-error mb-4">{String(errorMsg)}</p>
        )}

        <div className="flex justify-end gap-3">
          <Button variant="secondary" onClick={onClose} disabled={avanzar.isPending}>
            Cancelar
          </Button>
          <Button
            variant="primary"
            onClick={handleConfirm}
            loading={avanzar.isPending}
            disabled={avanzar.isPending}
          >
            Confirmar
          </Button>
        </div>
      </div>
    </Modal>
  )
}
