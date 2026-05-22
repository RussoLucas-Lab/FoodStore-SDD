/**
 * Skeleton — placeholder de carga con animación pulse.
 * Dimensiones configurables vía className.
 */

interface SkeletonProps {
  /** Clases adicionales para controlar width, height, border-radius, etc. */
  className?: string
}

export function Skeleton({ className = '' }: SkeletonProps) {
  return (
    <div
      className={`bg-border-color animate-pulse rounded-sm ${className}`}
      aria-hidden="true"
    />
  )
}

// ---------------------------------------------------------------------------
// Skeletons compuestos de uso frecuente
// ---------------------------------------------------------------------------

/** Skeleton para una tarjeta de producto */
export function ProductCardSkeleton() {
  return (
    <div className="bg-surface rounded-md p-4 flex flex-col gap-3">
      <Skeleton className="w-full h-48 rounded-sm" />
      <Skeleton className="w-3/4 h-5" />
      <Skeleton className="w-1/2 h-4" />
      <Skeleton className="w-1/4 h-6" />
    </div>
  )
}

/** Skeleton para un elemento de lista */
export function ListItemSkeleton() {
  return (
    <div className="flex items-center gap-4 p-4">
      <Skeleton className="w-12 h-12 rounded-full" />
      <div className="flex-1 flex flex-col gap-2">
        <Skeleton className="w-2/3 h-4" />
        <Skeleton className="w-1/2 h-3" />
      </div>
    </div>
  )
}
