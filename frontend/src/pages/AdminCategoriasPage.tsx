/**
 * AdminCategoriasPage — página de gestión de categorías.
 * Delegada al componente CategoriaCRUD del feature admin.
 */

import { CategoriaCRUD } from '@/features/admin/components/CategoriaCRUD'

export default function AdminCategoriasPage() {
  return (
    <div className="p-6">
      <CategoriaCRUD />
    </div>
  )
}
