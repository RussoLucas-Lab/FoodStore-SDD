import { useState, useEffect, useRef } from 'react'
import { useUsuariosAdmin } from '../hooks/useUsuariosAdmin'
import { UsuariosTable } from './UsuariosTable'
import { Skeleton } from '@/components/Skeleton'

export function UsuariosCRUD() {
  const [q, setQ] = useState('')
  const [debouncedQ, setDebouncedQ] = useState('')
  const [page, setPage] = useState(1)
  const timerRef = useRef<ReturnType<typeof setTimeout>>()

  useEffect(() => {
    clearTimeout(timerRef.current)
    timerRef.current = setTimeout(() => {
      setDebouncedQ(q)
      setPage(1)
    }, 300)
    return () => clearTimeout(timerRef.current)
  }, [q])

  const { data, isLoading } = useUsuariosAdmin({
    q: debouncedQ || undefined,
    page,
    size: 20,
  })

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-semibold text-text-primary">Gestión de usuarios</h1>

      <div className="flex items-center gap-3">
        <input
          type="text"
          placeholder="Buscar por nombre, apellido o email..."
          value={q}
          onChange={(e) => setQ(e.target.value)}
          className="w-80 px-3 py-2 rounded-lg border border-border-color text-sm focus:outline-none focus:ring-2 focus:ring-blue/30"
        />
      </div>

      {isLoading ? (
        <div className="flex flex-col gap-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </div>
      ) : !data || data.items.length === 0 ? (
        <p className="text-text-secondary text-sm">No se encontraron usuarios.</p>
      ) : (
        <UsuariosTable
          usuarios={data.items}
          total={data.total}
          page={data.page}
          pages={data.pages}
          onPageChange={setPage}
        />
      )}
    </div>
  )
}
