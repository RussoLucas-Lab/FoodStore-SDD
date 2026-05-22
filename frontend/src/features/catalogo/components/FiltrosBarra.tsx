import { useState, useEffect } from 'react'
import { useCategoriaTree } from '@/features/admin/hooks/useCategorias'

export interface FiltrosState {
  categoriaId: number | undefined
  q: string
}

interface FiltrosBarraProps {
  value: FiltrosState
  onChange: (filtros: FiltrosState) => void
}

export function FiltrosBarra({ value, onChange }: FiltrosBarraProps) {
  const { data: categorias } = useCategoriaTree()
  const [inputValue, setInputValue] = useState(value.q)

  // Debounce 300ms for text search
  useEffect(() => {
    const timer = setTimeout(() => {
      if (inputValue !== value.q) {
        onChange({ ...value, q: inputValue })
      }
    }, 300)
    return () => clearTimeout(timer)
  }, [inputValue]) // eslint-disable-line react-hooks/exhaustive-deps

  // Sync external q changes (e.g., clear)
  useEffect(() => {
    setInputValue(value.q)
  }, [value.q])

  const handleClear = () => {
    setInputValue('')
    onChange({ categoriaId: undefined, q: '' })
  }

  const hasFilters = value.categoriaId !== undefined || value.q !== ''

  // Flatten tree for select options
  const flatCategories: { id: number; nombre: string; level: number }[] = []
  function flatten(
    nodes: { id: number; nombre: string; subcategorias?: typeof nodes }[],
    level = 0,
  ) {
    for (const node of nodes) {
      flatCategories.push({ id: node.id, nombre: node.nombre, level })
      if (node.subcategorias && node.subcategorias.length > 0) {
        flatten(node.subcategorias, level + 1)
      }
    }
  }
  if (categorias) flatten(categorias)

  return (
    <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-center">
      {/* Búsqueda textual */}
      <input
        type="text"
        placeholder="Buscar producto..."
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        className="
          border border-border-color rounded-md px-3 py-2 text-sm
          bg-white text-text-primary placeholder-text-secondary
          focus:outline-none focus:ring-2 focus:ring-blue focus:border-transparent
          w-full sm:w-64
        "
      />

      {/* Selector de categoría */}
      <select
        value={value.categoriaId ?? ''}
        onChange={(e) =>
          onChange({
            ...value,
            categoriaId: e.target.value ? Number(e.target.value) : undefined,
          })
        }
        className="
          border border-border-color rounded-md px-3 py-2 text-sm
          bg-white text-text-primary
          focus:outline-none focus:ring-2 focus:ring-blue focus:border-transparent
          w-full sm:w-48
        "
      >
        <option value="">Todas las categorías</option>
        {flatCategories.map((cat) => (
          <option key={cat.id} value={cat.id}>
            {' '.repeat(cat.level * 2)}{cat.nombre}
          </option>
        ))}
      </select>

      {/* Limpiar filtros */}
      {hasFilters && (
        <button
          onClick={handleClear}
          className="text-sm text-text-secondary hover:text-error transition-colors underline whitespace-nowrap"
        >
          Limpiar filtros
        </button>
      )}
    </div>
  )
}
