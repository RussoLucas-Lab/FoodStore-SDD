import { useState } from 'react'
import type { UsuarioAdmin } from '@/types/admin'
import { useActivarUsuario } from '../hooks/useAdminMutations'
import { useUiStore } from '@/store/uiStore'
import { EditarRolesModal } from './EditarRolesModal'

interface UsuariosTableProps {
  usuarios: UsuarioAdmin[]
  total: number
  page: number
  pages: number
  onPageChange: (page: number) => void
}

const ROL_COLORS: Record<string, string> = {
  ADMIN: 'bg-red-100 text-red-700',
  STOCK: 'bg-blue-100 text-blue-700',
  PEDIDOS: 'bg-purple-100 text-purple-700',
  CLIENT: 'bg-gray-100 text-gray-700',
}

export function UsuariosTable({
  usuarios,
  total,
  page,
  pages,
  onPageChange,
}: UsuariosTableProps) {
  const [editingRolesUser, setEditingRolesUser] = useState<UsuarioAdmin | null>(null)
  const activarMutation = useActivarUsuario()
  const addToast = useUiStore((s) => s.addToast)

  function handleToggleActivo(usuario: UsuarioAdmin) {
    activarMutation.mutate(
      { id: usuario.id, activo: !usuario.activo },
      {
        onError: (err: unknown) => {
          const detail = (err as { response?: { data?: { detail?: string } } })
            ?.response?.data?.detail
          if (typeof detail === 'string' && detail.includes('LAST_ADMIN')) {
            addToast('No se puede desactivar al último administrador.', 'error')
          }
        },
      },
    )
  }

  return (
    <>
      <div className="overflow-x-auto rounded-xl border border-border-color">
        <table className="w-full text-sm">
          <thead className="bg-surface text-text-secondary">
            <tr>
              <th className="px-4 py-3 text-left font-medium">Nombre</th>
              <th className="px-4 py-3 text-left font-medium">Email</th>
              <th className="px-4 py-3 text-left font-medium">Roles</th>
              <th className="px-4 py-3 text-center font-medium">Activo</th>
              <th className="px-4 py-3 text-center font-medium">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border-color">
            {usuarios.map((u) => (
              <tr key={u.id} className="bg-white hover:bg-surface transition-colors">
                <td className="px-4 py-3 font-medium text-text-primary">
                  {u.nombre} {u.apellido}
                </td>
                <td className="px-4 py-3 text-text-secondary">{u.email}</td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-1">
                    {u.roles.map((rol) => (
                      <span
                        key={rol}
                        className={`px-2 py-0.5 rounded-full text-xs font-medium ${ROL_COLORS[rol] ?? 'bg-gray-100 text-gray-700'}`}
                      >
                        {rol}
                      </span>
                    ))}
                  </div>
                </td>
                <td className="px-4 py-3 text-center">
                  <button
                    onClick={() => handleToggleActivo(u)}
                    className={`relative inline-flex h-5 w-9 rounded-full transition-colors ${
                      u.activo ? 'bg-green-500' : 'bg-gray-300'
                    }`}
                    aria-label={u.activo ? 'Desactivar' : 'Activar'}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform mt-0.5 ${
                        u.activo ? 'translate-x-4' : 'translate-x-0.5'
                      }`}
                    />
                  </button>
                </td>
                <td className="px-4 py-3 text-center">
                  <button
                    onClick={() => setEditingRolesUser(u)}
                    className="text-xs text-blue hover:underline"
                  >
                    Editar roles
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {pages > 1 && (
        <div className="flex items-center justify-between text-sm text-text-secondary">
          <span>
            {total} usuario{total !== 1 ? 's' : ''}
          </span>
          <div className="flex gap-2">
            <button
              disabled={page <= 1}
              onClick={() => onPageChange(page - 1)}
              className="px-3 py-1 rounded border border-border-color disabled:opacity-40"
            >
              Anterior
            </button>
            <span className="px-3 py-1">
              {page} / {pages}
            </span>
            <button
              disabled={page >= pages}
              onClick={() => onPageChange(page + 1)}
              className="px-3 py-1 rounded border border-border-color disabled:opacity-40"
            >
              Siguiente
            </button>
          </div>
        </div>
      )}

      {editingRolesUser && (
        <EditarRolesModal
          usuario={editingRolesUser}
          onClose={() => setEditingRolesUser(null)}
        />
      )}
    </>
  )
}
