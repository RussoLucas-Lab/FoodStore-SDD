import { useState } from 'react'
import { Modal } from '@/components/Modal'
import type { UsuarioAdmin } from '@/types/admin'
import { useAsignarRoles } from '../hooks/useAdminMutations'
import { useAuthStore } from '@/store/authStore'

const ROLES_DISPONIBLES = ['ADMIN', 'STOCK', 'PEDIDOS', 'CLIENT']

interface EditarRolesModalProps {
  usuario: UsuarioAdmin
  onClose: () => void
}

export function EditarRolesModal({ usuario, onClose }: EditarRolesModalProps) {
  const [selectedRoles, setSelectedRoles] = useState<string[]>(usuario.roles)
  const asignarRolesMutation = useAsignarRoles()
  const currentUserId = useAuthStore((s) => s.usuario?.id)

  const isOwnUser = currentUserId === usuario.id

  function toggleRol(rol: string) {
    setSelectedRoles((prev) =>
      prev.includes(rol) ? prev.filter((r) => r !== rol) : [...prev, rol],
    )
  }

  function handleGuardar() {
    asignarRolesMutation.mutate(
      { id: usuario.id, roles: selectedRoles },
      { onSuccess: onClose },
    )
  }

  return (
    <Modal open onClose={onClose}>
      <div className="p-6 flex flex-col gap-4">
        <h2 className="text-base font-semibold text-text-primary">
          Editar roles — {usuario.nombre} {usuario.apellido}
        </h2>

        {isOwnUser && (
          <p className="text-sm text-amber-600 bg-amber-50 rounded-md px-3 py-2">
            No podés cambiar tus propios roles.
          </p>
        )}

        <div className="flex flex-col gap-2">
          {ROLES_DISPONIBLES.map((rol) => (
            <label
              key={rol}
              className="flex items-center gap-3 cursor-pointer p-2 rounded-md hover:bg-surface"
            >
              <input
                type="checkbox"
                checked={selectedRoles.includes(rol)}
                onChange={() => toggleRol(rol)}
                disabled={isOwnUser}
                className="h-4 w-4"
              />
              <span className="text-sm font-medium text-text-primary">{rol}</span>
            </label>
          ))}
        </div>

        <div className="flex justify-end gap-3 pt-2">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm rounded-lg border border-border-color text-text-secondary hover:bg-surface"
          >
            Cancelar
          </button>
          <button
            onClick={handleGuardar}
            disabled={isOwnUser || asignarRolesMutation.isPending}
            className="px-4 py-2 text-sm rounded-lg bg-blue text-white disabled:opacity-50"
          >
            {asignarRolesMutation.isPending ? 'Guardando...' : 'Guardar'}
          </button>
        </div>
      </div>
    </Modal>
  )
}
