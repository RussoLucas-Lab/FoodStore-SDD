/**
 * AddressSelector — selector de dirección de entrega con CRUD inline.
 *
 * Recibe selectedId y onSelect. Muestra lista de direcciones del usuario
 * con opciones de editar, eliminar y promover a principal.
 * Incluye formulario inline para alta rápida de nueva dirección.
 */

import { useState } from 'react'
import { Skeleton } from '@/components/Skeleton'
import {
  useDirecciones,
  useCreateDireccion,
  useUpdateDireccion,
  useSetPrincipal,
  useDeleteDireccion,
} from '../hooks/useDirecciones'
import { AddressForm } from './AddressForm'
import type { DireccionCreate, DireccionRead, DireccionUpdate } from '@/types/direcciones'

interface AddressSelectorProps {
  selectedId: number | null
  onSelect: (id: number | null) => void
}

function formatDireccion(d: DireccionRead): string {
  const partes = [d.calle, d.numero]
  if (d.piso) partes.push(`Piso ${d.piso}`)
  if (d.depto) partes.push(`Depto ${d.depto}`)
  partes.push(d.ciudad, d.provincia, d.codigo_postal)
  return partes.join(', ')
}

type FormMode = 'create' | { edit: DireccionRead } | null

export function AddressSelector({ selectedId, onSelect }: AddressSelectorProps) {
  const { data: direcciones = [], isLoading } = useDirecciones()
  const createMutation = useCreateDireccion()
  const updateMutation = useUpdateDireccion()
  const setPrincipalMutation = useSetPrincipal()
  const deleteMutation = useDeleteDireccion()

  const [formMode, setFormMode] = useState<FormMode>(null)

  // --- Create ---
  const handleCreate = (data: DireccionCreate | DireccionUpdate) => {
    createMutation.mutate(data as DireccionCreate, {
      onSuccess: (newDireccion) => {
        onSelect(newDireccion.id)
        setFormMode(null)
      },
    })
  }

  // --- Update ---
  const handleUpdate = (id: number, data: DireccionCreate | DireccionUpdate) => {
    updateMutation.mutate({ id, data: data as DireccionUpdate }, {
      onSuccess: () => {
        setFormMode(null)
      },
    })
  }

  // --- Delete ---
  const handleDelete = (d: DireccionRead) => {
    if (!window.confirm(`¿Eliminar la dirección "${formatDireccion(d)}"?`)) return

    deleteMutation.mutate(d.id, {
      onSuccess: () => {
        // Task 7.4: si era la seleccionada, auto-seleccionar la principal restante
        if (d.id === selectedId) {
          const restantes = direcciones.filter((dir) => dir.id !== d.id)
          const principal = restantes.find((dir) => dir.es_principal)
          onSelect(principal?.id ?? null)
        }
      },
    })
  }

  // --- Set principal ---
  const handleSetPrincipal = (id: number) => {
    setPrincipalMutation.mutate(id)
  }

  // --- Render ---
  if (isLoading) {
    return (
      <div className="flex flex-col gap-3">
        <Skeleton className="h-14 rounded" />
        <Skeleton className="h-14 rounded" />
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-3">
      {/* Lista de direcciones */}
      {direcciones.length === 0 && formMode === null && (
        <p className="text-text-secondary text-sm">Aún no tenés direcciones registradas.</p>
      )}

      {direcciones.map((d) => (
        <div
          key={d.id}
          className={`flex items-start gap-3 p-3 border rounded-md cursor-pointer transition-colors
            ${selectedId === d.id ? 'border-blue bg-blue/5' : 'border-border-color hover:border-blue/40'}
          `}
          onClick={() => onSelect(d.id)}
          role="radio"
          aria-checked={selectedId === d.id}
          tabIndex={0}
          onKeyDown={(e) => e.key === 'Enter' && onSelect(d.id)}
        >
          {/* Radio visual */}
          <div className="mt-0.5 flex-shrink-0">
            <div
              className={`w-4 h-4 rounded-full border-2 flex items-center justify-center
                ${selectedId === d.id ? 'border-blue' : 'border-border-color'}
              `}
            >
              {selectedId === d.id && (
                <div className="w-2 h-2 rounded-full bg-blue" />
              )}
            </div>
          </div>

          {/* Texto */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-text-primary text-sm">{formatDireccion(d)}</span>
              {d.es_principal && (
                <span className="inline-block bg-blue/10 text-blue text-xs font-medium px-2 py-0.5 rounded-full">
                  Principal
                </span>
              )}
            </div>
            {d.referencia && (
              <p className="text-xs text-text-secondary mt-0.5">{d.referencia}</p>
            )}

            {/* Acciones por item */}
            <div className="flex items-center gap-3 mt-1.5" onClick={(e) => e.stopPropagation()}>
              <button
                onClick={() => setFormMode({ edit: d })}
                className="text-xs text-text-secondary hover:text-blue transition-colors"
              >
                Editar
              </button>
              <button
                onClick={() => handleDelete(d)}
                disabled={deleteMutation.isPending}
                className="text-xs text-text-secondary hover:text-error transition-colors disabled:opacity-40"
              >
                Eliminar
              </button>
              {!d.es_principal && (
                <button
                  onClick={() => handleSetPrincipal(d.id)}
                  disabled={setPrincipalMutation.isPending}
                  className="text-xs text-text-secondary hover:text-blue transition-colors disabled:opacity-40"
                >
                  Hacer principal
                </button>
              )}
            </div>
          </div>
        </div>
      ))}

      {/* Formulario inline (alta o edición) */}
      {formMode === 'create' && (
        <AddressForm
          onSubmit={handleCreate}
          onCancel={() => setFormMode(null)}
          isPending={createMutation.isPending}
        />
      )}

      {formMode !== null && formMode !== 'create' && (
        <AddressForm
          initialValues={{
            calle: formMode.edit.calle,
            numero: formMode.edit.numero,
            piso: formMode.edit.piso ?? '',
            depto: formMode.edit.depto ?? '',
            ciudad: formMode.edit.ciudad,
            provincia: formMode.edit.provincia,
            codigo_postal: formMode.edit.codigo_postal,
            referencia: formMode.edit.referencia ?? '',
          }}
          onSubmit={(data) => handleUpdate(formMode.edit.id, data)}
          onCancel={() => setFormMode(null)}
          isPending={updateMutation.isPending}
        />
      )}

      {/* Link agregar dirección */}
      {formMode === null && (
        <button
          onClick={() => setFormMode('create')}
          className="text-blue text-sm font-medium hover:underline self-start"
        >
          + Agregar dirección
        </button>
      )}
    </div>
  )
}
