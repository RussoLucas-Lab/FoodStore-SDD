import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { productosApi } from '@/api/endpoints/productos'
import type { ProductoRead } from '@/types/productos'
import { useAuthStore } from '@/store/authStore'
import { Skeleton } from '@/components/Skeleton'

export function StockTable() {
  const [includeDeleted, setIncludeDeleted] = useState(false)
  const [editingStock, setEditingStock] = useState<Record<number, string>>({})
  const qc = useQueryClient()
  const userRol = useAuthStore((s) => s.usuario?.rol)
  const isAdmin = userRol === 'ADMIN'

  const { data, isLoading } = useQuery({
    queryKey: ['productos', 'admin-stock', includeDeleted],
    queryFn: () =>
      productosApi
        .getProductos({ size: 100, ...(includeDeleted ? { include_deleted: true } as Record<string, unknown> : {}) })
        .then((r) => r.data),
  })

  const disponibilidadMutation = useMutation({
    mutationFn: ({ id, disponible }: { id: number; disponible: boolean }) =>
      productosApi.patchDisponibilidad(id, { disponible }).then((r) => r.data),
    onMutate: async ({ id, disponible }) => {
      await qc.cancelQueries({ queryKey: ['productos', 'admin-stock', includeDeleted] })
      const prev = qc.getQueryData(['productos', 'admin-stock', includeDeleted])
      qc.setQueryData(['productos', 'admin-stock', includeDeleted], (old: typeof data) => {
        if (!old) return old
        return { ...old, items: old.items.map((p: ProductoRead) => p.id === id ? { ...p, disponible } : p) }
      })
      return { prev }
    },
    onError: (_err, _vars, context) => {
      if (context?.prev) {
        qc.setQueryData(['productos', 'admin-stock', includeDeleted], context.prev)
      }
    },
    onSettled: () => qc.invalidateQueries({ queryKey: ['productos', 'admin-stock'] }),
  })

  const stockMutation = useMutation({
    mutationFn: ({ id, cantidad }: { id: number; cantidad: number }) =>
      productosApi.patchStock(id, { cantidad }).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['productos', 'admin-stock'] }),
  })

  function handleStockBlur(producto: ProductoRead) {
    const raw = editingStock[producto.id]
    if (raw === undefined) return
    const cantidad = parseInt(raw, 10)
    if (!isNaN(cantidad) && cantidad !== producto.stock_cantidad) {
      stockMutation.mutate({ id: producto.id, cantidad })
    }
    setEditingStock((prev) => {
      const next = { ...prev }
      delete next[producto.id]
      return next
    })
  }

  const productos = data?.items ?? []

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-text-primary">Gestión de stock</h1>
        {isAdmin && (
          <label className="flex items-center gap-2 text-sm text-text-secondary cursor-pointer">
            <input
              type="checkbox"
              checked={includeDeleted}
              onChange={(e) => setIncludeDeleted(e.target.checked)}
              className="h-4 w-4"
            />
            Mostrar eliminados
          </label>
        )}
      </div>

      {isLoading ? (
        <div className="flex flex-col gap-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-border-color">
          <table className="w-full text-sm">
            <thead className="bg-surface text-text-secondary">
              <tr>
                <th className="px-4 py-3 text-left font-medium">Nombre</th>
                <th className="px-4 py-3 text-center font-medium">Stock</th>
                <th className="px-4 py-3 text-center font-medium">Disponible</th>
                {isAdmin && (
                  <th className="px-4 py-3 text-center font-medium">Estado</th>
                )}
              </tr>
            </thead>
            <tbody className="divide-y divide-border-color">
              {productos.map((p) => {
                const isDeleted = p.deleted_at !== null
                return (
                  <tr
                    key={p.id}
                    className={`bg-white hover:bg-surface transition-colors ${isDeleted ? 'opacity-60' : ''}`}
                  >
                    <td className="px-4 py-3 font-medium text-text-primary">
                      {p.nombre}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <input
                        type="number"
                        min={0}
                        value={editingStock[p.id] ?? p.stock_cantidad}
                        onChange={(e) =>
                          setEditingStock((prev) => ({ ...prev, [p.id]: e.target.value }))
                        }
                        onBlur={() => handleStockBlur(p)}
                        className="w-20 text-center border border-border-color rounded-md px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue/30"
                        disabled={isDeleted}
                      />
                    </td>
                    <td className="px-4 py-3 text-center">
                      <button
                        onClick={() =>
                          disponibilidadMutation.mutate({ id: p.id, disponible: !p.disponible })
                        }
                        disabled={isDeleted}
                        className={`relative inline-flex h-5 w-9 rounded-full transition-colors ${
                          p.disponible ? 'bg-green-500' : 'bg-gray-300'
                        } disabled:opacity-40`}
                        aria-label={p.disponible ? 'Deshabilitar' : 'Habilitar'}
                      >
                        <span
                          className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform mt-0.5 ${
                            p.disponible ? 'translate-x-4' : 'translate-x-0.5'
                          }`}
                        />
                      </button>
                    </td>
                    {isAdmin && (
                      <td className="px-4 py-3 text-center">
                        {isDeleted ? (
                          <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-700">
                            Eliminado
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700">
                            Activo
                          </span>
                        )}
                      </td>
                    )}
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
