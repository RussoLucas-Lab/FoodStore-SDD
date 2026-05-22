/**
 * CategoriaCRUD — gestión de categorías en el panel admin.
 *
 * Muestra el árbol jerárquico de categorías con acciones por nodo:
 *   - Editar, Agregar subcategoría, Eliminar
 * Incluye modal de creación/edición y confirmación de eliminación.
 */

import { useState } from 'react'
import { useForm } from '@tanstack/react-form'
import { Modal } from '@/components/Modal'
import { Button } from '@/components/Button'
import { Input } from '@/components/Input'
import { Skeleton } from '@/components/Skeleton'
import { useUiStore } from '@/store/uiStore'
import {
  useCategoriaTree,
  useCreateCategoria,
  useUpdateCategoria,
  useDeleteCategoria,
} from '../hooks/useCategorias'
import type { CategoriaCreate, CategoriaTreeRead, CategoriaUpdate } from '@/types/categorias'
import type { AxiosError } from 'axios'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface FormValues {
  nombre: string
  parent_id: string
}

interface ModalState {
  open: boolean
  mode: 'create' | 'edit'
  editId?: number
  initialValues?: FormValues
}

// ---------------------------------------------------------------------------
// CategoriaNode — nodo recursivo del árbol
// ---------------------------------------------------------------------------

interface CategoriaNodeProps {
  node: CategoriaTreeRead
  level: number
  onEdit: (node: CategoriaTreeRead) => void
  onAddChild: (parentId: number) => void
  onDelete: (node: CategoriaTreeRead) => void
}

function CategoriaNode({
  node,
  level,
  onEdit,
  onAddChild,
  onDelete,
}: CategoriaNodeProps) {
  const [expanded, setExpanded] = useState(true)
  const hasChildren = node.subcategorias.length > 0

  return (
    <div>
      <div
        className="flex items-center gap-2 py-2 px-3 rounded-sm hover:bg-surface group"
        style={{ paddingLeft: `${level * 20 + 12}px` }}
      >
        {/* Expand/Collapse toggle */}
        <button
          onClick={() => setExpanded((v) => !v)}
          className="w-5 h-5 flex items-center justify-center text-text-tertiary flex-shrink-0"
          aria-label={expanded ? 'Colapsar' : 'Expandir'}
        >
          {hasChildren ? (
            <span className="text-xs">{expanded ? '▼' : '▶'}</span>
          ) : (
            <span className="text-xs text-transparent">▶</span>
          )}
        </button>

        {/* Nombre */}
        <span className="flex-1 text-sm text-text-primary font-medium">
          {node.nombre}
        </span>

        {/* Badge inactiva */}
        {!node.activa && (
          <span className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">
            Inactiva
          </span>
        )}

        {/* Acciones — visibles en hover */}
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            onClick={() => onAddChild(node.id)}
            className="px-2 py-1 text-xs text-blue hover:bg-blue/10 rounded-sm"
            title="Agregar subcategoría"
          >
            + Sub
          </button>
          <button
            onClick={() => onEdit(node)}
            className="px-2 py-1 text-xs text-text-secondary hover:bg-surface rounded-sm"
            title="Editar"
          >
            Editar
          </button>
          <button
            onClick={() => onDelete(node)}
            className="px-2 py-1 text-xs text-error hover:bg-error/10 rounded-sm"
            title="Eliminar"
          >
            Eliminar
          </button>
        </div>
      </div>

      {/* Subcategorías recursivas */}
      {hasChildren && expanded && (
        <div>
          {node.subcategorias.map((sub) => (
            <CategoriaNode
              key={sub.id}
              node={sub}
              level={level + 1}
              onEdit={onEdit}
              onAddChild={onAddChild}
              onDelete={onDelete}
            />
          ))}
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// CategoriaFormModal
// ---------------------------------------------------------------------------

interface CategoriaFormModalProps {
  open: boolean
  mode: 'create' | 'edit'
  editId?: number
  initialValues?: FormValues
  allCategorias: CategoriaTreeRead[]
  onClose: () => void
}

function flattenTree(nodes: CategoriaTreeRead[]): CategoriaTreeRead[] {
  const result: CategoriaTreeRead[] = []
  for (const node of nodes) {
    result.push(node)
    result.push(...flattenTree(node.subcategorias))
  }
  return result
}

function CategoriaFormModal({
  open,
  mode,
  editId,
  initialValues,
  allCategorias,
  onClose,
}: CategoriaFormModalProps) {
  const addToast = useUiStore((s) => s.addToast)
  const createCategoria = useCreateCategoria()
  const updateCategoria = useUpdateCategoria()

  const flatList = flattenTree(allCategorias).filter((c) => c.id !== editId)

  const form = useForm<FormValues>({
    defaultValues: initialValues ?? { nombre: '', parent_id: '' },
    onSubmit: async ({ value }) => {
      const parentId = value.parent_id ? parseInt(value.parent_id, 10) : null

      if (mode === 'create') {
        const body: CategoriaCreate = {
          nombre: value.nombre.trim(),
          parent_id: parentId,
        }
        createCategoria.mutate(body, {
          onSuccess: () => {
            addToast('Categoría creada correctamente.', 'success')
            onClose()
          },
          onError: () => {
            addToast('Error al crear la categoría.', 'error')
          },
        })
      } else if (mode === 'edit' && editId !== undefined) {
        const body: CategoriaUpdate = {
          nombre: value.nombre.trim() || undefined,
          parent_id: parentId,
        }
        updateCategoria.mutate(
          { id: editId, data: body },
          {
            onSuccess: () => {
              addToast('Categoría actualizada correctamente.', 'success')
              onClose()
            },
            onError: () => {
              addToast('Error al actualizar la categoría.', 'error')
            },
          },
        )
      }
    },
  })

  const isPending = createCategoria.isPending || updateCategoria.isPending

  return (
    <Modal open={open} onClose={onClose}>
      <div className="p-6">
        <h2 className="text-lg font-semibold text-text-primary mb-4">
          {mode === 'create' ? 'Nueva categoría' : 'Editar categoría'}
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
                placeholder="Nombre de la categoría"
                required
              />
            )}
          </form.Field>

          {/* Categoría padre (opcional) */}
          <form.Field name="parent_id">
            {(field) => (
              <div className="flex flex-col gap-1.5">
                <label className="text-sm font-medium text-text-primary">
                  Categoría padre (opcional)
                </label>
                <select
                  value={field.state.value}
                  onChange={(e) => field.handleChange(e.target.value)}
                  className="w-full px-4 py-2.5 text-sm text-text-primary bg-white border border-border-color rounded-sm focus:outline-none focus:border-blue focus:ring-1 focus:ring-blue"
                >
                  <option value="">— Sin padre (categoría raíz) —</option>
                  {flatList.map((cat) => (
                    <option key={cat.id} value={String(cat.id)}>
                      {cat.nombre}
                    </option>
                  ))}
                </select>
              </div>
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
// CategoriaCRUD — componente principal
// ---------------------------------------------------------------------------

export function CategoriaCRUD() {
  const { data: tree, isLoading, isError } = useCategoriaTree()
  const deleteCategoria = useDeleteCategoria()
  const addToast = useUiStore((s) => s.addToast)
  const openConfirm = useUiStore((s) => s.openConfirm)

  const [modal, setModal] = useState<ModalState>({
    open: false,
    mode: 'create',
  })

  function handleOpenCreate() {
    setModal({ open: true, mode: 'create', initialValues: { nombre: '', parent_id: '' } })
  }

  function handleOpenCreateChild(parentId: number) {
    setModal({
      open: true,
      mode: 'create',
      initialValues: { nombre: '', parent_id: String(parentId) },
    })
  }

  function handleOpenEdit(node: CategoriaTreeRead) {
    setModal({
      open: true,
      mode: 'edit',
      editId: node.id,
      initialValues: {
        nombre: node.nombre,
        parent_id: node.parent_id ? String(node.parent_id) : '',
      },
    })
  }

  function handleDelete(node: CategoriaTreeRead) {
    openConfirm({
      title: 'Eliminar categoría',
      message: `¿Estás seguro que querés eliminar "${node.nombre}"? Esta acción no se puede deshacer.`,
      confirmLabel: 'Eliminar',
      variant: 'danger',
      onConfirm: () => {
        deleteCategoria.mutate(node.id, {
          onSuccess: () => {
            addToast('Categoría eliminada correctamente.', 'success')
          },
          onError: (error: unknown) => {
            const axiosError = error as AxiosError<{ code?: string; detail?: string }>
            const code = axiosError.response?.data?.code
            if (code === 'RN_CA03') {
              addToast(
                'No se puede eliminar: la categoría tiene productos activos asociados.',
                'error',
              )
            } else if (code === 'CATEGORIA_HAS_CHILDREN') {
              addToast(
                'No se puede eliminar: la categoría tiene subcategorías activas.',
                'error',
              )
            } else {
              addToast('Error al eliminar la categoría.', 'error')
            }
          },
        })
      },
    })
  }

  function handleCloseModal() {
    setModal((s) => ({ ...s, open: false }))
  }

  // --- Skeleton ---
  if (isLoading) {
    return (
      <div className="flex flex-col gap-3 p-4">
        {[1, 2, 3, 4].map((i) => (
          <Skeleton key={i} className="h-10 w-full" />
        ))}
      </div>
    )
  }

  if (isError) {
    return (
      <div className="p-4 text-error text-sm">
        Error al cargar las categorías. Intente nuevamente.
      </div>
    )
  }

  return (
    <div className="bg-white rounded-md shadow-sm border border-border-color">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border-color">
        <h2 className="text-base font-semibold text-text-primary">Categorías</h2>
        <Button onClick={handleOpenCreate} className="text-sm">
          + Nueva categoría
        </Button>
      </div>

      {/* Árbol */}
      <div className="p-2">
        {!tree || tree.length === 0 ? (
          <p className="text-sm text-text-tertiary text-center py-8">
            No hay categorías. Crea la primera.
          </p>
        ) : (
          tree.map((node) => (
            <CategoriaNode
              key={node.id}
              node={node}
              level={0}
              onEdit={handleOpenEdit}
              onAddChild={handleOpenCreateChild}
              onDelete={handleDelete}
            />
          ))
        )}
      </div>

      {/* Modal de formulario */}
      <CategoriaFormModal
        open={modal.open}
        mode={modal.mode}
        editId={modal.editId}
        initialValues={modal.initialValues}
        allCategorias={tree ?? []}
        onClose={handleCloseModal}
      />
    </div>
  )
}
