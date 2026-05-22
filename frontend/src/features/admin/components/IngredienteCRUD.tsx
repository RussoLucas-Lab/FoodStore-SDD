/**
 * IngredienteCRUD — gestión de ingredientes en el panel admin.
 *
 * Tabla paginada con:
 *   - Badge "Alérgeno" para es_alergeno=true
 *   - Filtro "Solo alérgenos"
 *   - Modal de crear/editar
 *   - Confirmación de eliminación
 */

import { useState } from 'react'
import { useForm } from '@tanstack/react-form'
import { Modal } from '@/components/Modal'
import { Button } from '@/components/Button'
import { Input } from '@/components/Input'
import { Skeleton } from '@/components/Skeleton'
import { useUiStore } from '@/store/uiStore'
import {
  useIngredientes,
  useCreateIngrediente,
  useUpdateIngrediente,
  useDeleteIngrediente,
} from '../hooks/useIngredientes'
import type { IngredienteCreate, IngredienteRead, IngredienteUpdate } from '@/types/ingredientes'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface IngredienteFormValues {
  nombre: string
  es_alergeno: boolean
}

interface IngredienteModalState {
  open: boolean
  mode: 'create' | 'edit'
  editId?: number
  initialValues?: IngredienteFormValues
}

// ---------------------------------------------------------------------------
// AlergenoBadge
// ---------------------------------------------------------------------------

function AlergenoBadge({ esAlergeno }: { esAlergeno: boolean }) {
  if (!esAlergeno) return null
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-orange-100 text-orange-700 border border-orange-200">
      Alérgeno
    </span>
  )
}

// ---------------------------------------------------------------------------
// IngredienteFormModal
// ---------------------------------------------------------------------------

interface IngredienteFormModalProps {
  open: boolean
  mode: 'create' | 'edit'
  editId?: number
  initialValues?: IngredienteFormValues
  onClose: () => void
}

function IngredienteFormModal({
  open,
  mode,
  editId,
  initialValues,
  onClose,
}: IngredienteFormModalProps) {
  const addToast = useUiStore((s) => s.addToast)
  const createIngrediente = useCreateIngrediente()
  const updateIngrediente = useUpdateIngrediente()

  const form = useForm<IngredienteFormValues>({
    defaultValues: initialValues ?? { nombre: '', es_alergeno: false },
    onSubmit: async ({ value }) => {
      if (mode === 'create') {
        const body: IngredienteCreate = {
          nombre: value.nombre.trim(),
          es_alergeno: value.es_alergeno,
        }
        createIngrediente.mutate(body, {
          onSuccess: () => {
            addToast('Ingrediente creado correctamente.', 'success')
            onClose()
          },
          onError: () => {
            addToast('Error al crear el ingrediente.', 'error')
          },
        })
      } else if (mode === 'edit' && editId !== undefined) {
        const body: IngredienteUpdate = {
          nombre: value.nombre.trim() || undefined,
          es_alergeno: value.es_alergeno,
        }
        updateIngrediente.mutate(
          { id: editId, data: body },
          {
            onSuccess: () => {
              addToast('Ingrediente actualizado correctamente.', 'success')
              onClose()
            },
            onError: () => {
              addToast('Error al actualizar el ingrediente.', 'error')
            },
          },
        )
      }
    },
  })

  const isPending = createIngrediente.isPending || updateIngrediente.isPending

  return (
    <Modal open={open} onClose={onClose}>
      <div className="p-6">
        <h2 className="text-lg font-semibold text-text-primary mb-4">
          {mode === 'create' ? 'Nuevo ingrediente' : 'Editar ingrediente'}
        </h2>

        <form
          onSubmit={(e) => {
            e.preventDefault()
            form.handleSubmit()
          }}
          className="flex flex-col gap-4"
        >
          {/* Nombre */}
          <form.Field
            name="nombre"
            validators={{
              onChange: ({ value }) =>
                !value.trim() ? 'El nombre es obligatorio.' : undefined,
            }}
          >
            {(field) => (
              <Input
                label="Nombre"
                value={field.state.value}
                onChange={(e) => field.handleChange(e.target.value)}
                onBlur={field.handleBlur}
                error={field.state.meta.errors[0]}
                placeholder="Nombre del ingrediente"
                required
              />
            )}
          </form.Field>

          {/* Checkbox es_alergeno */}
          <form.Field name="es_alergeno">
            {(field) => (
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={field.state.value}
                  onChange={(e) => field.handleChange(e.target.checked)}
                  className="w-4 h-4 text-blue border-border-color rounded focus:ring-blue"
                />
                <span className="text-sm font-medium text-text-primary">
                  Es alérgeno
                </span>
              </label>
            )}
          </form.Field>

          {/* Acciones */}
          <div className="flex justify-end gap-3 pt-2">
            <Button type="button" variant="secondary" onClick={onClose}>
              Cancelar
            </Button>
            <Button type="submit" loading={isPending}>
              {mode === 'create' ? 'Crear' : 'Guardar cambios'}
            </Button>
          </div>
        </form>
      </div>
    </Modal>
  )
}

// ---------------------------------------------------------------------------
// IngredienteCRUD — componente principal
// ---------------------------------------------------------------------------

export function IngredienteCRUD() {
  const [page, setPage] = useState(1)
  const [soloAlergenos, setSoloAlergenos] = useState(false)

  const { data, isLoading, isError } = useIngredientes({
    page,
    size: 20,
    es_alergeno: soloAlergenos ? true : undefined,
  })

  const deleteIngrediente = useDeleteIngrediente()
  const addToast = useUiStore((s) => s.addToast)
  const openConfirm = useUiStore((s) => s.openConfirm)

  const [modal, setModal] = useState<IngredienteModalState>({
    open: false,
    mode: 'create',
  })

  function handleOpenCreate() {
    setModal({ open: true, mode: 'create', initialValues: { nombre: '', es_alergeno: false } })
  }

  function handleOpenEdit(ing: IngredienteRead) {
    setModal({
      open: true,
      mode: 'edit',
      editId: ing.id,
      initialValues: { nombre: ing.nombre, es_alergeno: ing.es_alergeno },
    })
  }

  function handleDelete(ing: IngredienteRead) {
    openConfirm({
      title: 'Eliminar ingrediente',
      message: `¿Estás seguro que querés eliminar "${ing.nombre}"?`,
      confirmLabel: 'Eliminar',
      variant: 'danger',
      onConfirm: () => {
        deleteIngrediente.mutate(ing.id, {
          onSuccess: () => {
            addToast('Ingrediente eliminado correctamente.', 'success')
          },
          onError: () => {
            addToast('Error al eliminar el ingrediente.', 'error')
          },
        })
      },
    })
  }

  function handleCloseModal() {
    setModal((s) => ({ ...s, open: false }))
  }

  const totalPages = data?.pages ?? 1

  return (
    <div className="bg-white rounded-md shadow-sm border border-border-color">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border-color flex-wrap gap-3">
        <h2 className="text-base font-semibold text-text-primary">Ingredientes</h2>
        <div className="flex items-center gap-3">
          {/* Filtro alergenos */}
          <label className="flex items-center gap-2 text-sm text-text-secondary cursor-pointer">
            <input
              type="checkbox"
              checked={soloAlergenos}
              onChange={(e) => {
                setSoloAlergenos(e.target.checked)
                setPage(1)
              }}
              className="w-4 h-4 text-orange-500 border-border-color rounded"
            />
            Solo alérgenos
          </label>
          <Button onClick={handleOpenCreate} className="text-sm">
            + Nuevo ingrediente
          </Button>
        </div>
      </div>

      {/* Contenido */}
      {isLoading ? (
        <div className="flex flex-col gap-2 p-4">
          {[1, 2, 3, 4, 5].map((i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </div>
      ) : isError ? (
        <div className="p-4 text-error text-sm">
          Error al cargar los ingredientes. Intente nuevamente.
        </div>
      ) : (
        <>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border-color bg-surface">
                <th className="text-left px-4 py-3 text-text-secondary font-medium">Nombre</th>
                <th className="text-left px-4 py-3 text-text-secondary font-medium">Alérgeno</th>
                <th className="text-right px-4 py-3 text-text-secondary font-medium">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {!data?.items || data.items.length === 0 ? (
                <tr>
                  <td colSpan={3} className="text-center py-8 text-text-tertiary">
                    No hay ingredientes.{' '}
                    {soloAlergenos ? 'No se encontraron alérgenos.' : 'Crea el primero.'}
                  </td>
                </tr>
              ) : (
                data.items.map((ing) => (
                  <tr
                    key={ing.id}
                    className="border-b border-border-color last:border-0 hover:bg-surface/50 transition-colors"
                  >
                    <td className="px-4 py-3 text-text-primary font-medium">{ing.nombre}</td>
                    <td className="px-4 py-3">
                      <AlergenoBadge esAlergeno={ing.es_alergeno} />
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => handleOpenEdit(ing)}
                          className="px-3 py-1.5 text-xs text-text-secondary hover:bg-surface rounded-sm border border-border-color transition-colors"
                        >
                          Editar
                        </button>
                        <button
                          onClick={() => handleDelete(ing)}
                          className="px-3 py-1.5 text-xs text-error hover:bg-error/10 rounded-sm border border-error/30 transition-colors"
                        >
                          Eliminar
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>

          {/* Paginación */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between px-4 py-3 border-t border-border-color">
              <span className="text-xs text-text-tertiary">
                Página {page} de {totalPages} · {data?.total} ingredientes
              </span>
              <div className="flex items-center gap-2">
                <Button
                  variant="secondary"
                  className="text-xs px-3 py-1.5"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                >
                  Anterior
                </Button>
                <Button
                  variant="secondary"
                  className="text-xs px-3 py-1.5"
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                >
                  Siguiente
                </Button>
              </div>
            </div>
          )}
        </>
      )}

      {/* Modal */}
      <IngredienteFormModal
        open={modal.open}
        mode={modal.mode}
        editId={modal.editId}
        initialValues={modal.initialValues}
        onClose={handleCloseModal}
      />
    </div>
  )
}
