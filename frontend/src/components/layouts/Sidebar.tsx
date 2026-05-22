import { NavLink } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import type { Rol } from '@/types/auth'

interface SidebarItem {
  label: string
  to: string
  roles: Rol[]
}

const ITEMS: SidebarItem[] = [
  { label: 'Dashboard', to: '/admin', roles: ['ADMIN'] },
  {
    label: 'Stock',
    to: '/admin/stock',
    roles: ['ADMIN', 'STOCK'],
  },
  {
    label: 'Categorías',
    to: '/admin/categorias',
    roles: ['ADMIN', 'STOCK'],
  },
  {
    label: 'Ingredientes',
    to: '/admin/ingredientes',
    roles: ['ADMIN', 'STOCK'],
  },
  {
    label: 'Pedidos',
    to: '/admin/pedidos',
    roles: ['ADMIN', 'PEDIDOS'],
  },
  { label: 'Usuarios', to: '/admin/usuarios', roles: ['ADMIN'] },
  { label: 'Configuración', to: '/admin/configuracion', roles: ['ADMIN'] },
]

export function Sidebar() {
  const usuario = useAuthStore((s) => s.usuario)
  const rol = usuario?.rol as Rol | undefined

  const visibleItems = rol
    ? ITEMS.filter((item) => item.roles.includes(rol))
    : []

  return (
    <aside className="w-56 shrink-0 border-r border-border-color bg-white min-h-screen pt-6">
      <nav className="flex flex-col gap-1 px-3">
        {visibleItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/admin'}
            className={({ isActive }) =>
              `px-3 py-2 rounded-md text-sm transition-colors ${
                isActive
                  ? 'bg-blue/10 text-blue font-medium'
                  : 'text-text-secondary hover:text-text-primary hover:bg-surface'
              }`
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
