/**
 * CancelarPedidoModal — modal de confirmación para cancelar un pedido propio.
 *
 * - Campo de texto "motivo" requerido.
 * - Botón confirmar deshabilitado si motivo está vacío.
 * - Llama useCancelarPedido() al confirmar.
 * - Muestra errores inline de la API.
 */

import { useState } from 'react'
import { Modal } from '@/components/Modal'
import { Button } from '@/components/Button'
import { useCancelarPedido } from '../hooks/useCancelarPedido'

interface CancelarPedidoModalProps {
  open: boolean
  onClose: () => void
  pedidoId: number
  onSuccess?: () => void
}

export function CancelarPedidoModal({
  open,
  onClose,
  pedidoId,
  onSuccess,
}: CancelarPedidoModalProps) {
  const [motivo, setMotivo] = useState('')
  const [apiError, setApiError] = useState<string | null>(null)
  const cancelar = useCancelarPedido()

  function handleClose() {
    setMotivo('')
    setApiError(null)
    onClose()
  }

  function handleConfirm() {
    if (!motivo.trim()) return
    setApiError(null)

    cancelar.mutate(
      { id: pedidoId, motivo: motivo.trim() },
      {
        onSuccess: () => {
          handleClose()
          onSuccess?.()
        },
        onError: (error) => {
          const msg =
            (error as { response?: { data?: { detail?: string } } }).response?.data?.detail ??
            'Error al cancelar el pedido. Intente nuevamente.'
          setApiError(String(msg))
        },
      },
    )
  }

  return (
    <Modal open={open} onClose={handleClose} maxWidth="max-w-md">
      <div className="p-6">
        <h2 className="text-lg font-semibold text-text-primary mb-1">
          Cancelar pedido
        </h2>
        <p className="text-sm text-text-secondary mb-4">
          Esta acción no se puede deshacer. Por favor indicá el motivo de la cancelación.
        </p>

        <label htmlFor="motivo-cancelacion" className="block text-sm font-medium text-text-primary mb-1">
          Motivo <span className="text-error">*</span>
        </label>
        <textarea
          id="motivo-cancelacion"
          value={motivo}
          onChange={(e) => setMotivo(e.target.value)}
          rows={3}
          placeholder="Ej: Ya no puedo recibirlo hoy"
          className="w-full border border-border-color rounded-md px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue"
        />

        {apiError && (
          <p className="mt-2 text-sm text-error" role="alert">
            {apiError}
          </p>
        )}

        <div className="flex justify-end gap-3 mt-5">
          <Button variant="secondary" onClick={handleClose} disabled={cancelar.isPending}>
            Volver
          </Button>
          <Button
            variant="primary"
            onClick={handleConfirm}
            disabled={!motivo.trim() || cancelar.isPending}
            loading={cancelar.isPending}
            className="bg-red-600 hover:bg-red-700 focus-visible:ring-red-600"
          >
            Confirmar cancelación
          </Button>
        </div>
      </div>
    </Modal>
  )
}
