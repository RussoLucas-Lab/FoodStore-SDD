import { Skeleton } from '@/components/Skeleton'
import { useFormasPago } from '../hooks/useFormasPago'

interface PaymentMethodSelectorProps {
  selectedCodigo: string | null
  onSelect: (codigo: string) => void
}

export function PaymentMethodSelector({ selectedCodigo, onSelect }: PaymentMethodSelectorProps) {
  const { data: formas, isLoading, isError, refetch } = useFormasPago()

  if (isLoading) {
    return (
      <div className="flex flex-col gap-2">
        <Skeleton className="h-12 rounded" />
        <Skeleton className="h-12 rounded" />
        <Skeleton className="h-12 rounded" />
      </div>
    )
  }

  if (isError) {
    return (
      <div className="text-sm text-text-secondary flex flex-col gap-2">
        <p>No se pudieron cargar las formas de pago.</p>
        <button
          onClick={() => refetch()}
          className="text-blue hover:underline self-start text-sm font-medium"
        >
          Reintentar
        </button>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-2">
      {(formas ?? []).map((forma) => (
        <div
          key={forma.codigo}
          className={`flex items-center gap-3 p-3 border rounded-md cursor-pointer transition-colors
            ${selectedCodigo === forma.codigo ? 'border-blue bg-blue/5' : 'border-border-color hover:border-blue/40'}
          `}
          onClick={() => onSelect(forma.codigo)}
          role="radio"
          aria-checked={selectedCodigo === forma.codigo}
          tabIndex={0}
          onKeyDown={(e) => e.key === 'Enter' && onSelect(forma.codigo)}
        >
          <div className="flex-shrink-0">
            <div
              className={`w-4 h-4 rounded-full border-2 flex items-center justify-center
                ${selectedCodigo === forma.codigo ? 'border-blue' : 'border-border-color'}
              `}
            >
              {selectedCodigo === forma.codigo && (
                <div className="w-2 h-2 rounded-full bg-blue" />
              )}
            </div>
          </div>
          <span className="text-sm text-text-primary">{forma.descripcion ?? forma.codigo}</span>
        </div>
      ))}
    </div>
  )
}
