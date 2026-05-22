/**
 * Button — componente de botón reutilizable.
 *
 * Variantes:
 *   - primary: fondo #0071E3, texto blanco, borde redondeado pill
 *   - secondary: fondo transparente, texto #0071E3, borde redondeado pill
 */

import { type ButtonHTMLAttributes } from 'react'
import { Spinner } from './Spinner'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary'
  loading?: boolean
}

export function Button({
  variant = 'primary',
  loading = false,
  disabled,
  children,
  className = '',
  ...props
}: ButtonProps) {
  const base =
    'inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-full font-medium text-sm transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed'

  const variants = {
    primary:
      'bg-blue text-white hover:bg-blue-dark active:scale-95 focus-visible:ring-blue',
    secondary:
      'bg-transparent text-blue border border-blue hover:bg-blue/5 active:scale-95 focus-visible:ring-blue',
  }

  return (
    <button
      disabled={disabled || loading}
      className={`${base} ${variants[variant]} ${className}`}
      {...props}
    >
      {loading && <Spinner size="sm" color="current" />}
      {children}
    </button>
  )
}
