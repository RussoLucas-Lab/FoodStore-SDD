/**
 * AdminIngredientesPage — página de gestión de ingredientes.
 * Delegada al componente IngredienteCRUD del feature admin.
 */

import { IngredienteCRUD } from '@/features/admin/components/IngredienteCRUD'

export default function AdminIngredientesPage() {
  return (
    <div className="p-6">
      <IngredienteCRUD />
    </div>
  )
}
