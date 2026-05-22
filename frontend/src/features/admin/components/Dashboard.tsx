import { useMetricasResumen } from '../hooks/useMetricasResumen'
import { KpiCard } from './KpiCard'
import { VentasLineChart } from './VentasLineChart'
import { ProductosTopBarChart } from './ProductosTopBarChart'
import { PedidosPieChart } from './PedidosPieChart'

export function Dashboard() {
  const { data, isLoading } = useMetricasResumen()

  return (
    <div className="flex flex-col gap-8">
      <h1 className="text-2xl font-semibold text-text-primary">Dashboard</h1>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <KpiCard
          title="Total pedidos"
          value={data?.total_pedidos}
          isLoading={isLoading}
        />
        <KpiCard
          title="Ventas del mes"
          value={data?.ventas_mes !== undefined ? Number(data.ventas_mes).toFixed(2) : undefined}
          isLoading={isLoading}
          prefix="$"
        />
        <KpiCard
          title="Productos activos"
          value={data?.productos_activos}
          isLoading={isLoading}
        />
        <KpiCard
          title="Usuarios activos"
          value={data?.usuarios_activos}
          isLoading={isLoading}
        />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <VentasLineChart />
        <PedidosPieChart />
      </div>

      <ProductosTopBarChart />
    </div>
  )
}
