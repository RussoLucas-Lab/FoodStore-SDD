/**
 * AgregarAlCarritoModal — modal de personalización antes de agregar al carrito.
 *
 * Permite excluir ingredientes (tope RN-CR04: n_ingredientes - 1).
 * Ajusta cantidad mínima 1.
 * Al confirmar: dispatcha addItem al cartStore.
 */

import { useState } from 'react'
import { Modal } from '@/components/Modal'
import { useCartStore } from '@/store/cartStore'
import type { ProductoRead, IngredienteSimple } from '@/types/productos'

interface AgregarAlCarritoModalProps {
  producto: ProductoRead
  open: boolean
  onClose: () => void
}

export function AgregarAlCarritoModal({ producto, open, onClose }: AgregarAlCarritoModalProps) {
  const [cantidad, setCantidad] = useState(1)
  const [excluidos, setExcluidos] = useState<Set<number>>(new Set())
  const addItem = useCartStore((s) => s.addItem)

  const ingredientes: IngredienteSimple[] = producto.ingredientes ?? []
  const maxExcluidos = Math.max(0, ingredientes.length - 1)

  const handleToggleExcluir = (id: number) => {
    setExcluidos((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else if (next.size < maxExcluidos) {
        next.add(id)
      }
      return next
    })
  }

  const handleConfirmar = () => {
    const excluidosArray = [...excluidos]
    const excluidosNombres = ingredientes
      .filter((i) => excluidos.has(i.id))
      .map((i) => i.nombre)

    addItem(
      {
        id: producto.id,
        nombre: producto.nombre,
        precio_base: producto.precio_base,
      },
      cantidad,
      excluidosArray,
      excluidosNombres,
    )

    // Reset y cerrar
    setCantidad(1)
    setExcluidos(new Set())
    onClose()
  }

  const handleClose = () => {
    setCantidad(1)
    setExcluidos(new Set())
    onClose()
  }

  return (
    <Modal open={open} onClose={handleClose} maxWidth="max-w-md">
      <div className="p-6 flex flex-col gap-5">
        {/* Header */}
        <div>
          <h2 className="text-text-primary font-semibold text-lg">Personalizá tu pedido</h2>
          <p className="text-text-secondary text-sm mt-0.5">{producto.nombre}</p>
        </div>

        {/* Ingredientes */}
        {ingredientes.length === 0 ? (
          <p className="text-text-secondary text-sm">
            Este producto no tiene ingredientes personalizables.
          </p>
        ) : (
          <div className="flex flex-col gap-2">
            <p className="text-text-secondary text-xs font-medium uppercase tracking-wide">
              Excluir ingredientes (máx. {maxExcluidos})
            </p>
            <div className="flex flex-col gap-1.5 max-h-48 overflow-y-auto">
              {ingredientes.map((ing) => {
                const isChecked = excluidos.has(ing.id)
                const isDisabled = !isChecked && excluidos.size >= maxExcluidos
                return (
                  <label
                    key={ing.id}
                    className={`flex items-center gap-3 p-2 rounded cursor-pointer select-none
                      ${isDisabled ? 'opacity-40 cursor-not-allowed' : 'hover:bg-surface-alt'}
                    `}
                    title={isDisabled ? 'Tenés que mantener al menos un ingrediente' : undefined}
                  >
                    <input
                      type="checkbox"
                      checked={isChecked}
                      disabled={isDisabled}
                      onChange={() => handleToggleExcluir(ing.id)}
                      className="h-4 w-4 accent-blue"
                    />
                    <span className="text-text-primary text-sm">{ing.nombre}</span>
                    {ing.es_alergeno && (
                      <span className="text-xs text-red-600 font-medium ml-auto">Alérgeno</span>
                    )}
                  </label>
                )
              })}
            </div>
          </div>
        )}

        {/* Control de cantidad */}
        <div className="flex items-center gap-4">
          <span className="text-text-secondary text-sm">Cantidad</span>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setCantidad((c) => Math.max(1, c - 1))}
              disabled={cantidad <= 1}
              className="w-8 h-8 rounded-full border border-border-color flex items-center justify-center text-text-secondary hover:bg-surface-alt disabled:opacity-40 transition-colors"
              aria-label="Disminuir cantidad"
            >
              −
            </button>
            <span className="text-text-primary font-semibold w-6 text-center">{cantidad}</span>
            <button
              onClick={() => setCantidad((c) => c + 1)}
              className="w-8 h-8 rounded-full border border-border-color flex items-center justify-center text-text-secondary hover:bg-surface-alt transition-colors"
              aria-label="Aumentar cantidad"
            >
              +
            </button>
          </div>
        </div>

        {/* Acciones */}
        <div className="flex gap-3 pt-1">
          <button
            onClick={handleClose}
            className="flex-1 py-2.5 rounded-full border border-border-color text-text-secondary text-sm font-medium hover:bg-surface-alt transition-colors"
          >
            Cancelar
          </button>
          <button
            onClick={handleConfirmar}
            className="flex-1 py-2.5 rounded-full bg-blue text-white text-sm font-medium hover:bg-blue-dark transition-colors"
          >
            Agregar al carrito
          </button>
        </div>
      </div>
    </Modal>
  )
}
