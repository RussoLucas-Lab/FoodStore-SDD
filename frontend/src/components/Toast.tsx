/**
 * Toast — notificaciones temporales.
 *
 * Variantes:
 *   - success: #34C759
 *   - error:   #FF3B30
 *
 * Se auto-descarta luego de `duration` ms (por defecto 4000).
 * Para manejar múltiples toasts usa ToastContainer con un array de ToastItem.
 */

import { useEffect, useState } from 'react'

export interface ToastItem {
  id: string
  message: string
  variant: 'success' | 'error'
  duration?: number
}

interface ToastProps extends ToastItem {
  onDismiss: (id: string) => void
}

export function Toast({ id, message, variant, duration = 4000, onDismiss }: ToastProps) {
  const [visible, setVisible] = useState(true)

  useEffect(() => {
    const timer = setTimeout(() => {
      setVisible(false)
      setTimeout(() => onDismiss(id), 300) // esperar animación de salida
    }, duration)
    return () => clearTimeout(timer)
  }, [id, duration, onDismiss])

  const variantClasses = {
    success: 'bg-success text-white',
    error: 'bg-error text-white',
  }

  const icons = {
    success: '✓',
    error: '✕',
  }

  return (
    <div
      role="alert"
      aria-live="polite"
      className={`
        flex items-center gap-3 px-4 py-3 rounded-sm shadow-card
        text-sm font-medium
        transition-all duration-300
        ${variantClasses[variant]}
        ${visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-2'}
      `}
    >
      <span className="text-lg leading-none" aria-hidden="true">
        {icons[variant]}
      </span>
      <span>{message}</span>
      <button
        onClick={() => onDismiss(id)}
        className="ml-auto opacity-70 hover:opacity-100 transition-opacity"
        aria-label="Cerrar notificación"
      >
        ✕
      </button>
    </div>
  )
}

// ---------------------------------------------------------------------------
// ToastContainer — contenedor de toasts (posición fija, bottom-right)
// ---------------------------------------------------------------------------

interface ToastContainerProps {
  toasts: ToastItem[]
  onDismiss: (id: string) => void
}

export function ToastContainer({ toasts, onDismiss }: ToastContainerProps) {
  return (
    <div
      className="fixed bottom-6 right-6 z-50 flex flex-col gap-3 max-w-sm w-full"
      aria-label="Notificaciones"
    >
      {toasts.map((toast) => (
        <Toast key={toast.id} {...toast} onDismiss={onDismiss} />
      ))}
    </div>
  )
}
