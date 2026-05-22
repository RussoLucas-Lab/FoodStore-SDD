import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { useProductosTop } from '../hooks/useProductosTop'
import { Skeleton } from '@/components/Skeleton'

export function ProductosTopBarChart() {
  const { data, isLoading } = useProductosTop(10)
  const items = data?.items ?? []

  return (
    <div className="bg-white rounded-xl border border-border-color p-6 flex flex-col gap-4">
      <h3 className="text-sm font-medium text-text-primary">Top 10 productos vendidos</h3>

      {isLoading ? (
        <Skeleton className="h-48 w-full" />
      ) : items.length === 0 ? (
        <div className="h-48 flex items-center justify-center text-text-secondary text-sm">
          Sin datos de ventas
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={items} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis type="number" tick={{ fontSize: 11 }} />
            <YAxis
              dataKey="nombre"
              type="category"
              tick={{ fontSize: 10 }}
              width={100}
            />
            <Tooltip
              formatter={(value: number) => [value, 'Unidades']}
            />
            <Bar dataKey="unidades_vendidas" fill="#3b82f6" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}
