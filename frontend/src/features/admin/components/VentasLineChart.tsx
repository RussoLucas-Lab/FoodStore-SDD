import { useState } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { useVentasPorPeriodo, type Periodo } from '../hooks/useVentasPorPeriodo'
import { Skeleton } from '@/components/Skeleton'

const PERIODOS: { label: string; value: Periodo }[] = [
  { label: 'Día', value: 'dia' },
  { label: 'Semana', value: 'semana' },
  { label: 'Mes', value: 'mes' },
]

export function VentasLineChart() {
  const [periodo, setPeriodo] = useState<Periodo>('mes')
  const { data, isLoading } = useVentasPorPeriodo(periodo)

  const series = data?.series ?? []

  return (
    <div className="bg-white rounded-xl border border-border-color p-6 flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-text-primary">Ventas por período</h3>
        <div className="flex gap-1">
          {PERIODOS.map((p) => (
            <button
              key={p.value}
              onClick={() => setPeriodo(p.value)}
              className={`px-3 py-1 rounded-md text-xs transition-colors ${
                periodo === p.value
                  ? 'bg-blue/10 text-blue font-medium'
                  : 'text-text-secondary hover:text-text-primary'
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <Skeleton className="h-48 w-full" />
      ) : series.length === 0 ? (
        <div className="h-48 flex items-center justify-center text-text-secondary text-sm">
          Sin datos para este período
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={series}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="fecha" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip
              formatter={(value) => [`$${Number(value).toFixed(2)}`, 'Total']}
            />
            <Line
              type="monotone"
              dataKey="total"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}
