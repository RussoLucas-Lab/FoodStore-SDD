/**
 * Card — contenedor con superficie #F5F5F7, border-radius 18px y padding 40px.
 */

import { type HTMLAttributes } from 'react'

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  /** Elimina el padding por defecto (útil para cards con contenido que necesita sangrar) */
  noPadding?: boolean
}

export function Card({ noPadding = false, className = '', children, ...props }: CardProps) {
  return (
    <div
      className={`
        bg-surface rounded-md shadow-card
        ${noPadding ? '' : 'p-10'}
        ${className}
      `}
      {...props}
    >
      {children}
    </div>
  )
}
