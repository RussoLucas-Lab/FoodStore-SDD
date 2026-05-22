import { useState } from 'react'
import type { ProductoRead } from '@/types/productos'
import { AgregarAlCarritoModal } from './AgregarAlCarritoModal'

interface ProductoCardProps {
  producto: ProductoRead
}

const arsFormatter = new Intl.NumberFormat('es-AR', {
  style: 'currency',
  currency: 'ARS',
})

export function ProductoCard({ producto }: ProductoCardProps) {
  const [modalOpen, setModalOpen] = useState(false)
  const alergenos = producto.ingredientes.filter((i) => i.es_alergeno)

  return (
    <>
      <div className="relative bg-surface rounded-md shadow-card overflow-hidden flex flex-col">
        {/* Imagen */}
        <div className="relative w-full h-48 bg-border-color">
          {producto.imagen_url ? (
            <img
              src={producto.imagen_url}
              alt={producto.nombre}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-text-secondary text-sm">
              Sin imagen
            </div>
          )}

          {/* Overlay "No disponible" */}
          {!producto.disponible && (
            <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
              <span className="text-white font-semibold text-sm tracking-wide uppercase">
                No disponible
              </span>
            </div>
          )}
        </div>

        {/* Contenido */}
        <div className="p-4 flex flex-col gap-2 flex-1">
          <h3 className="text-text-primary font-semibold text-base leading-tight">
            {producto.nombre}
          </h3>

          {producto.descripcion && (
            <p className="text-text-secondary text-sm line-clamp-2 leading-relaxed">
              {producto.descripcion}
            </p>
          )}

          {/* Alérgenos */}
          {alergenos.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1">
              {alergenos.map((a) => (
                <span
                  key={a.id}
                  className="inline-block bg-red-100 text-red-700 text-xs font-medium px-2 py-0.5 rounded-full"
                >
                  {a.nombre}
                </span>
              ))}
            </div>
          )}

          {/* Precio */}
          <p className="text-text-primary font-bold text-lg mt-auto pt-2">
            {arsFormatter.format(Number(producto.precio_base))}
          </p>

          {/* Botón agregar al carrito */}
          <button
            onClick={() => setModalOpen(true)}
            disabled={!producto.disponible}
            className="mt-1 w-full py-2 rounded-full bg-blue text-white text-sm font-medium
              hover:bg-blue-dark transition-colors
              disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Agregar al carrito
          </button>
        </div>
      </div>

      {/* Modal de personalización */}
      <AgregarAlCarritoModal
        producto={producto}
        open={modalOpen}
        onClose={() => setModalOpen(false)}
      />
    </>
  )
}
