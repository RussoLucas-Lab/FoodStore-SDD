/**
 * Modal — diálogo centrado con overlay oscuro.
 *
 * Design tokens:
 *   - overlay: rgba(0, 0, 0, 0.4)
 *   - shadow: 0 40px 80px rgba(0, 0, 0, 0.2)
 *   - border-radius: 18px
 */

import { type ReactNode, useEffect } from 'react'

interface ModalProps {
  open: boolean
  onClose: () => void
  children: ReactNode
  /** Ancho máximo del modal (clase Tailwind, por defecto max-w-md) */
  maxWidth?: string
  /** Si true, no cierra al hacer clic en el overlay */
  preventClose?: boolean
}

export function Modal({
  open,
  onClose,
  children,
  maxWidth = 'max-w-md',
  preventClose = false,
}: ModalProps) {
  // Bloquear scroll del body cuando el modal está abierto
  useEffect(() => {
    if (open) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
    return () => {
      document.body.style.overflow = ''
    }
  }, [open])

  // Cerrar con Escape
  useEffect(() => {
    if (!open) return
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !preventClose) {
        onClose()
      }
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [open, onClose, preventClose])

  if (!open) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
    >
      {/* Overlay */}
      <div
        className="absolute inset-0 bg-black/40 backdrop-blur-sm"
        onClick={preventClose ? undefined : onClose}
        aria-hidden="true"
      />

      {/* Contenido */}
      <div
        className={`
          relative z-10 w-full ${maxWidth}
          bg-white rounded-md shadow-modal
          animate-in fade-in zoom-in-95 duration-200
        `}
      >
        {children}
      </div>
    </div>
  )
}
