import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts'
import { usePedidosPorEstado } from '../hooks/usePedidosPorEstado'
import { Skeleton } from '@/components/Skeleton'

const COLORS: Record<string, string> = {
  PENDIENTE: '#f59e0b',
  CONFIRMADO: '#3b82f6',
  EN_PREP: '#8b5cf6',
  EN_CAMINO: '#06b6d4',
  ENTREGADO: '#10b981',
  CANCELADO: '#ef4444',
}

const DEFAULT_COLOR = '#94a3b8'

export function PedidosPieChart() {
  const { data, isLoading } = usePedidosPorEstado()
  const items = data?.items ?? []

  return (
    <div className="bg-white rounded-xl border border-border-color p-6 flex flex-col gap-4">
      <h3 className="text-sm font-medium text-text-primary">Pedidos por estado</h3>

      {isLoading ? (
        <Skeleton className="h-48 w-full" />
      ) : items.length === 0 ? (
        <div className="h-48 flex items-center justify-center text-text-secondary text-sm">
          Sin pedidos registrados
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={200}>
          <PieChart>
            <Pie
              data={items}
              dataKey="cantidad"
              nameKey="estado"
              cx="50%"
              cy="50%"
              outerRadius={70}
              label={({ name, percent }) =>
                `${name} ${(percent * 100).toFixed(0)}%`
              }
              labelLine={false}
            >
              {items.map((entry) => (
                <Cell
                  key={entry.estado}
                  fill={COLORS[entry.estado] ?? DEFAULT_COLOR}
                />
              ))}
            </Pie>
            <Tooltip formatter={(value: number) => [value, 'Pedidos']} />
          </PieChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}
